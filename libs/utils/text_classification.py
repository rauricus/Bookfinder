"""
Text region sorting utilities for book spine text analysis.

This module provides functionality to sort text regions detected on book spines
in a more reliable way that handles multi-line text properly.
"""

from typing import Dict, List, Tuple, Any

from libs.logging import get_logger

logger = get_logger(__name__)


class TextRegionSorter:
    """
    Sorter for text regions on book spines.
    
    Provides improved sorting that handles multi-line text and ensures
    proper top-to-bottom, left-to-right ordering.
    """

    @staticmethod
    def sort_boxes_by_position(boxes: List[Tuple[int, int, int, int]], image=None, debug=0) -> Dict:
        """
        Sort bounding boxes by position using adaptive grid-based clustering.
        
        Algorithm:
        1. Calculate center points for all boxes
        2. Find natural column boundaries by analyzing X-coordinate gaps
        3. Group boxes into columns based on these boundaries
        4. Sort each column vertically (top-to-bottom, handling multi-line text)
        5. Concatenate columns left-to-right to get final sorted order
        
        Args:
            boxes: List of bounding boxes (x1, y1, x2, y2)
            image: Image for visualization (optional)
            debug: Debug level for visualization

        Returns:
            Dict: Structure information containing columns and rows
        """
        if not boxes:
            return {'columns': [], 'column_boundaries': [], 'total_columns': 0}
        
        # Step 1: Calculate center points for each box
        boxes_with_centers = []
        for x1, y1, x2, y2 in boxes:
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            boxes_with_centers.append(((x1, y1, x2, y2), center_x, center_y))

        # Step 2: Find natural column
        columns, column_boundaries = TextRegionSorter._find_natural_columns(boxes_with_centers)
        
        # Step 3: Sort boxes within each column vertically and get row structure
        column_structure = []
        
        for column in columns:
            rows = TextRegionSorter._sort_column_vertically(column)
            column_structure.append(rows)
        
        detected_structure = {
            'columns': column_structure,
            'total_columns': len(columns),
            'column_boundaries': column_boundaries
        }
        
        logger.debug(f"Sorted {len(boxes)} bounding boxes into {len(columns)} columns")
        
        # Visualize bounding boxes if debug level is high enough
        if debug >= 1 and image is not None:
            if not TextRegionSorter._showBoundingBoxes(image, boxes):
                logger.warning("User aborted execution during bounding box visualization.")
                return {}

            if not TextRegionSorter._showColumnRowStructure(image, detected_structure):
                logger.warning("User aborted execution during structure visualization.")
                return {}

        return detected_structure
    
    
    @staticmethod
    def _find_natural_columns(boxes_with_centers):
        """
        Find natural column boundaries based on actual gaps between boxes.
        Uses dynamic gap threshold based on text box heights for better adaptability.
        
        Algorithm:
        1. Calculate dynamic gap threshold based on text heights
        2. Sort boxes by left edge (x1) to properly analyze gaps between boxes
        3. Calculate actual gaps: right_box.x1 - left_box.x2
        4. Find significant gaps (>dynamic_gap_size) as column boundaries
        5. Group boxes into columns based on these boundaries
        
        Args:
            boxes_with_centers: List of tuples (box, center_x, center_y)
            
        Returns:
            Tuple of (columns, column_boundaries) where column_boundaries are X-coordinates
        """
        if not boxes_with_centers:
            return []
        
        # Calculate dynamic gap threshold based on text box heights
        min_gap_size = TextRegionSorter._calculate_dynamic_gap_threshold(boxes_with_centers)
        
        # Sort boxes by left edge (x1) to properly analyze gaps between boxes
        sorted_boxes = sorted(boxes_with_centers, key=lambda b: b[0][0])  # Sort by x1
        
        # Find actual gaps between consecutive boxes
        gaps = []
        
        for i in range(1, len(sorted_boxes)):
            left_box = sorted_boxes[i-1][0]   # (x1, y1, x2, y2)
            right_box = sorted_boxes[i][0]    # (x1, y1, x2, y2)
            
            # Calculate actual gap: right_box.x1 - left_box.x2
            actual_gap = right_box[0] - left_box[2]
            
            if actual_gap > min_gap_size:
                # Use the middle of the gap as boundary
                gap_center = left_box[2] + actual_gap / 2
                gaps.append(gap_center)
        
        # Remove duplicate gap positions (within small tolerance)
        unique_gaps = []
        gap_tolerance = 5  # pixels
        for gap in sorted(gaps):
            if not unique_gaps or abs(gap - unique_gaps[-1]) > gap_tolerance:
                unique_gaps.append(gap)
        
        # Group boxes into columns based on gap boundaries
        # Algorithm: For each box, count how many gaps are to its left to determine column index
        columns = []
        
        for box, center_x, center_y in boxes_with_centers:
            # Determine which column this box belongs to
            column_index = 0
            for gap in unique_gaps:
                if center_x > gap:
                    column_index += 1
                else:
                    break
            
            # Ensure we have enough columns
            while len(columns) <= column_index:
                columns.append([])
            
            columns[column_index].append((box, center_x, center_y))
        
        return columns, unique_gaps
    
    
    @staticmethod
    def _sort_column_vertically(column):
        """
        Sort boxes within a column vertically and group them into rows.
        
        Returns:
            List of detected, sorted rows.
        """
        if not column:
            return [], []
        
        # Group by similar Y-coordinates (same line within column)
        y_tolerance = 20  # pixels - boxes within this Y-distance are considered same row
        rows = []
        
        # Sort by Y-coordinate first
        column_by_y = sorted(column, key=lambda b: b[2])  # Sort by center_y
        
        # Group consecutive boxes with similar Y-coordinates into rows
        current_row = [column_by_y[0]]
        for i in range(1, len(column_by_y)):
            current_box = column_by_y[i]
            prev_box = column_by_y[i-1]
            
            y_diff = abs(current_box[2] - prev_box[2])
            if y_diff <= y_tolerance:
                # Add to current row
                current_row.append(current_box)
            else:
                # Start new row - sort current row by X-coordinate (left-to-right)
                sorted_row = sorted(current_row, key=lambda b: b[1])  # Sort by center_x
                rows.append([box for box, center_x, center_y in sorted_row])
                current_row = [current_box]
        
        # Add the last row
        if current_row:
            sorted_row = sorted(current_row, key=lambda b: b[1])
            rows.append([box for box, center_x, center_y in sorted_row])
        
        return rows
    
    
    @staticmethod
    def _calculate_dynamic_gap_threshold(boxes_with_centers):
        """
        Calculate an intelligent gap threshold using multiple factors:
        1. Text box heights (font size indicator)
        2. Actual gap distribution (what gaps already exist)
        3. Layout analysis (detect natural breaks between word-gaps and column-gaps)
        
        This provides better separation between word-gaps and column-gaps,
        solving issues like "Jaron Lanier" | "Title" separation.
        
        Args:
            boxes_with_centers: List of tuples (box, center_x, center_y)
            
        Returns:
            int: Smart gap threshold in pixels
        """
        if not boxes_with_centers:
            return 80  # Fallback to original value
        
        # Factor 1: Text height analysis (as baseline, but more conservative)
        heights = []
        for (x1, y1, x2, y2), center_x, center_y in boxes_with_centers:
            height = y2 - y1
            if height > 0:  # Only consider valid heights
                heights.append(height)
        
        if not heights:
            return 80  # Fallback if no valid heights found
        
        heights.sort()
        median_height = heights[len(heights) // 2]
        height_based_threshold = median_height * 1.5  # Reduced from 2.0 to be more sensitive
        
        # Factor 2: Actual gap analysis - examine existing gaps between boxes
        sorted_boxes = sorted(boxes_with_centers, key=lambda b: b[0][0])  # Sort by x1
        actual_gaps = []
        
        for i in range(1, len(sorted_boxes)):
            left_box = sorted_boxes[i-1][0]   # (x1, y1, x2, y2)
            right_box = sorted_boxes[i][0]    # (x1, y1, x2, y2)
            gap = right_box[0] - left_box[2]  # actual gap: right.x1 - left.x2
            if gap > 0:  # Only positive gaps
                actual_gaps.append(gap)
        
        if not actual_gaps:
            # No gaps found, use height-based threshold with bounds
            final_threshold = max(30, min(120, height_based_threshold))
            logger.debug(f"Smart gap calculation: no gaps found, using height-based={final_threshold:.1f}")
            return int(final_threshold)
        
        # Factor 3: Find natural break in gap distribution
        # This distinguishes between word-spacing (small gaps) and column-spacing (large gaps)
        actual_gaps.sort()
        gap_jump_threshold = None
        
        if len(actual_gaps) >= 2:
            gap_ratios = []
            for i in range(1, len(actual_gaps)):
                if actual_gaps[i-1] > 0:  # Avoid division by zero
                    ratio = actual_gaps[i] / actual_gaps[i-1]
                    gap_ratios.append((ratio, actual_gaps[i], actual_gaps[i-1]))
            
            # Find largest ratio jump (indicates transition from word-gaps to column-gaps)
            if gap_ratios:
                max_ratio, large_gap, small_gap = max(gap_ratios, key=lambda x: x[0])
                if max_ratio > 2.0:  # Significant jump indicates column separation
                    # Use a threshold slightly below the large gap
                    gap_jump_threshold = large_gap * 0.8
                    logger.debug(f"Gap jump detected: {small_gap:.1f} -> {large_gap:.1f} (ratio={max_ratio:.1f})")
        
        # Factor 4: Combine factors intelligently
        candidates = [height_based_threshold]
        if gap_jump_threshold is not None:
            candidates.append(gap_jump_threshold)
        
        # Choose the most conservative (lowest) reasonable threshold
        # This ensures we don't miss column separations due to being too aggressive
        smart_threshold = min(candidates)
        
        # Apply reasonable bounds - use lower minimum for gap_jump_threshold cases
        if gap_jump_threshold is not None:
            # When we detected a natural break, trust it with lower minimum
            final_threshold = max(10, min(150, smart_threshold))
        else:
            # Without natural break detection, use higher minimum for safety
            final_threshold = max(25, min(150, smart_threshold))
        
        logger.debug(f"Smart gap calculation: "
                    f"median_height={median_height:.1f}, "
                    f"height_based={height_based_threshold:.1f}, "
                    f"gap_jump={gap_jump_threshold}, "
                    f"smart={smart_threshold:.1f}, "
                    f"final={final_threshold:.1f}, "
                    f"gaps={actual_gaps}")
        
        return int(final_threshold)
    
    
    @staticmethod
    def _showBoundingBoxes(image, boxes):
        """
        Visualizes the bounding boxes on the input image.
        
        Returns:
            bool: True if user wants to continue, False if user pressed ESC to abort
        """
        import cv2

        # Create a copy to avoid modifying the original image
        display_image = image.copy()

        # Prepare window title based on content
        if boxes is None or len(boxes) == 0:
            logger.debug("No bounding boxes to display.")
            window_title = "Bounding boxes (No text regions detected)"
        else:
            window_title = f"Bounding boxes ({len(boxes)} text regions found)"
            
            # Show bounding boxes
            for i, (startX, startY, endX, endY) in enumerate(boxes):
                # Draw the lines
                cv2.rectangle(display_image, (startX, startY), (endX, endY), color=(0, 255, 0), thickness=2)

                # Add the index label
                text_x, text_y = startX+10, startY+40
                cv2.putText(display_image, f"{i}", (text_x, text_y),
                            fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1.2,
                            color=(0, 255, 0), thickness=2)

        # Add informational text overlay
        info_text = "Press any key to continue, ESC to abort"
        cv2.putText(display_image, info_text, (10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                    color=(255, 255, 255), thickness=2)
        cv2.putText(display_image, info_text, (10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                    color=(0, 0, 0), thickness=1)
        
        # Display the image with bounding boxes
        cv2.imshow(window_title, display_image)
        
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()
        
        # Give some time for proper window cleanup
        cv2.waitKey(1)

        if key == 27:  # ESC key
            logger.warning("ESC key pressed. Aborting execution.")
            return False
        
        return True

    @staticmethod
    def _showColumnRowStructure(image, detected_structure):
        """
        Visualizes the detected column and row structure on the input image.
        
        Args:
            image: Input image to draw on
            detected_structure: Dictionary containing structure information from TextRegionSorter
            
        Returns:
            bool: True if user wants to continue, False if user pressed ESC to abort
        """
        import cv2
        
        # Create a copy to avoid modifying the original image
        display_image = image.copy()
        
        # Define colors for visualization
        column_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
        row_color = (128, 128, 128)
        boundary_color = (255, 255, 255)
        
        total_columns = detected_structure.get('total_columns', 0)
        columns = detected_structure.get('columns', [])
        column_boundaries = detected_structure.get('column_boundaries', [])
        
        # Prepare window title
        window_title = f"Column/Row Structure ({total_columns} columns detected)"
        
        # Draw column boundaries as vertical lines
        image_height = display_image.shape[0]
        for boundary_x in column_boundaries:
            cv2.line(display_image, (int(boundary_x), 0), (int(boundary_x), image_height), 
                    boundary_color, thickness=3)
            
            # Add boundary label
            cv2.putText(display_image, "COL", (int(boundary_x) - 15, 25),
                       fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.6,
                       color=boundary_color, thickness=2)
        
        # Draw columns and rows
        for col_idx, column_rows in enumerate(columns):
            color = column_colors[col_idx % len(column_colors)]
            
            # Draw each row within the column
            for row_idx, row_boxes in enumerate(column_rows):
                if not row_boxes:
                    continue
                    
                # Calculate row bounding box
                min_x = min(box[0] for box in row_boxes)
                min_y = min(box[1] for box in row_boxes)
                max_x = max(box[2] for box in row_boxes)
                max_y = max(box[3] for box in row_boxes)
                
                # Draw row background with transparency effect
                overlay = display_image.copy()
                cv2.rectangle(overlay, (min_x - 5, min_y - 5), (max_x + 5, max_y + 5), 
                             color, thickness=-1)
                cv2.addWeighted(overlay, 0.2, display_image, 0.8, 0, display_image)
                
                # Draw row border
                cv2.rectangle(display_image, (min_x - 5, min_y - 5), (max_x + 5, max_y + 5), 
                             color, thickness=2)
                
                # Add row label
                label = f"C{col_idx+1}R{row_idx+1}"
                text_x = min_x
                text_y = min_y - 10 if min_y > 20 else max_y + 20
                
                # Draw text with outline for better visibility
                cv2.putText(display_image, label, (text_x, text_y),
                           fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                           color=(255, 255, 255), thickness=3)
                cv2.putText(display_image, label, (text_x, text_y),
                           fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                           color=color, thickness=2)
        
        # Add legend
        legend_y = 40
        cv2.putText(display_image, f"Detected: {total_columns} columns", (10, legend_y),
                   fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
                   color=(255, 255, 255), thickness=3)
        cv2.putText(display_image, f"Detected: {total_columns} columns", (10, legend_y),
                   fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.8,
                   color=(0, 0, 0), thickness=2)
        
        # Add usage instructions
        info_text = "Press any key to continue, ESC to abort"
        cv2.putText(display_image, info_text, (10, image_height - 20),
                   fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                   color=(255, 255, 255), thickness=2)
        cv2.putText(display_image, info_text, (10, image_height - 20),
                   fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.7,
                   color=(0, 0, 0), thickness=1)
        
        # Display the image
        cv2.imshow(window_title, display_image)
        
        # Wait for key press
        key = cv2.waitKey(0) & 0xFF
        cv2.destroyAllWindows()
        
        # Give some time for proper window cleanup
        cv2.waitKey(1)

        if key == 27:  # ESC key
            logger.warning("ESC key pressed. Aborting execution.")
            return False
        
        return True
