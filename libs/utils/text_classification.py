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
        Calculate a dynamic gap threshold based on the heights of text boxes.
        
        The idea: Larger text (higher boxes) should have proportionally larger gaps
        between columns. This makes the algorithm more robust across different font sizes.
        
        Args:
            boxes_with_centers: List of tuples (box, center_x, center_y)
            
        Returns:
            int: Dynamic gap threshold in pixels
        """
        if not boxes_with_centers:
            return 80  # Fallback to original value
        
        # Extract box heights
        heights = []
        for (x1, y1, x2, y2), center_x, center_y in boxes_with_centers:
            height = y2 - y1
            if height > 0:  # Only consider valid heights
                heights.append(height)
        
        if not heights:
            return 80  # Fallback if no valid heights found
        
        # Calculate statistical measures of box heights
        heights.sort()
        median_height = heights[len(heights) // 2]
        
        # For additional robustness, we can also consider the average of middle 50% of heights
        # This helps ignore extreme outliers (very small or very large boxes)
        q1_idx = len(heights) // 4
        q3_idx = 3 * len(heights) // 4
        middle_heights = heights[q1_idx:q3_idx] if len(heights) >= 4 else heights
        typical_height = sum(middle_heights) / len(middle_heights) if middle_heights else median_height
        
        # Calculate dynamic threshold
        # Rule of thumb: Gap should be at least 1.5-2.5 times the typical text height
        # This ensures clear separation between distinct columns while avoiding false splits
        base_multiplier = 2.0  # Base multiplier for typical text height
        min_threshold = 40     # Absolute minimum gap size (for very small text)
        max_threshold = 200    # Absolute maximum gap size (to prevent over-sensitivity)
        
        dynamic_threshold = typical_height * base_multiplier
        
        # Apply bounds to keep threshold reasonable
        final_threshold = max(min_threshold, min(max_threshold, dynamic_threshold))
        
        logger.debug(f"Dynamic gap calculation: typical_height={typical_height:.1f}, "
                    f"median_height={median_height:.1f}, dynamic_threshold={dynamic_threshold:.1f}, "
                    f"final_threshold={final_threshold:.1f}")
        
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
