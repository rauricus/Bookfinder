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
    def sort_boxes_by_position(boxes: List[Tuple[int, int, int, int]]) -> Tuple[List[Tuple[int, int, int, int]], Dict]:
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
        
        Returns:
            Tuple of (sorted_boxes, structure_info) where structure_info contains:
            - 'columns': List of columns, each containing rows
            - 'column_boundaries': List of X-coordinates where columns are separated
            - 'total_columns': Number of detected columns
        """
        if not boxes:
            return [], {'columns': [], 'column_boundaries': [], 'total_columns': 0}
        
        # Step 1: Calculate center points for each box
        boxes_with_centers = []
        for x1, y1, x2, y2 in boxes:
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            boxes_with_centers.append(((x1, y1, x2, y2), center_x, center_y))

        # Step 2: Find natural column boundaries and get detailed info
        columns, column_boundaries = TextRegionSorter._find_natural_columns_with_info(boxes_with_centers)
        
        # Step 3: Sort boxes within each column vertically and get row structure
        sorted_boxes = []
        column_structure = []
        
        for column in columns:
            sorted_column, rows = TextRegionSorter._sort_column_vertically_with_info(column)
            sorted_boxes.extend(sorted_column)
            column_structure.append(rows)
        
        structure_info = {
            'columns': column_structure,
            'column_boundaries': column_boundaries,
            'total_columns': len(columns)
        }
        
        logger.debug(f"Sorted {len(sorted_boxes)} bounding boxes into {len(columns)} columns with structure info")
        
        return sorted_boxes, structure_info
    
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
        
        # Apply reasonable bounds
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
            List of columns, each containing boxes belonging to that column
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
        
        # Return only non-empty columns
        return [col for col in columns if col]

    @staticmethod
    def _find_natural_columns_with_info(boxes_with_centers):
        """
        Find natural column boundaries and return both columns and boundary information.
        Uses dynamic gap threshold based on text box heights for better adaptability.
        
        Returns:
            Tuple of (columns, column_boundaries) where column_boundaries are X-coordinates
        """
        if not boxes_with_centers:
            return [], []
        
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
        
        # Return only non-empty columns and the gap boundaries
        return [col for col in columns if col], unique_gaps

    @staticmethod
    def _sort_column_vertically_with_info(column):
        """
        Sort boxes within a column vertically and return row information.
        
        Returns:
            Tuple of (sorted_boxes, rows) where rows contains row structure information
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
        
        # Flatten rows back to single list of boxes
        sorted_boxes = []
        for row in rows:
            sorted_boxes.extend(row)
        
        return sorted_boxes, rows

    @staticmethod
    def _sort_column_vertically(column):
        """
        Sort boxes within a column vertically, handling multi-line text properly.
        
        Algorithm:
        1. Sort all boxes in column by Y-coordinate
        2. Group boxes with similar Y-coordinates into rows (within tolerance)
        3. Sort each row by X-coordinate (left-to-right)
        4. Flatten rows back to single list maintaining top-to-bottom order
        
        Args:
            column: List of tuples (box, center_x, center_y) belonging to one column
            
        Returns:
            List of boxes sorted vertically within the column
        """
        if not column:
            return []
        
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
                rows.append(sorted(current_row, key=lambda b: b[1]))  # Sort by center_x
                current_row = [current_box]
        
        # Add the last row
        if current_row:
            rows.append(sorted(current_row, key=lambda b: b[1]))
        
        # Flatten rows back to single list of boxes
        sorted_boxes = []
        for row in rows:
            for box, center_x, center_y in row:
                sorted_boxes.append(box)
        
        return sorted_boxes
