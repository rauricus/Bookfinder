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
    def sort_boxes_by_position(boxes: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
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
            List of boxes sorted by position (columns left-to-right, within columns top-to-bottom)
        """
        if not boxes:
            return []
        
        # Step 1: Calculate center points for each box
        boxes_with_centers = []
        for x1, y1, x2, y2 in boxes:
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2
            boxes_with_centers.append(((x1, y1, x2, y2), center_x, center_y))

        # Step 2: Find natural column boundaries using gap analysis
        columns = TextRegionSorter._find_natural_columns(boxes_with_centers)
        
        # Step 3: Sort boxes within each column vertically
        sorted_boxes = []
        for column in columns:
            sorted_column = TextRegionSorter._sort_column_vertically(column)
            sorted_boxes.extend(sorted_column)
        
        logger.debug(f"Sorted {len(sorted_boxes)} bounding boxes into {len(columns)} columns")
        
        return sorted_boxes
    
    @staticmethod
    def _find_natural_columns(boxes_with_centers):
        """
        Find natural column boundaries based on actual gaps between boxes.
        
        Algorithm:
        1. Sort boxes by left edge (x1) to properly analyze gaps between boxes
        2. Calculate actual gaps: right_box.x1 - left_box.x2
        3. Find significant gaps (>min_gap_size) as column boundaries
        4. Group boxes into columns based on these boundaries
        
        Args:
            boxes_with_centers: List of tuples (box, center_x, center_y)
            
        Returns:
            List of columns, each containing boxes belonging to that column
        """
        if not boxes_with_centers:
            return []
        
        # Sort boxes by left edge (x1) to properly analyze gaps between boxes
        sorted_boxes = sorted(boxes_with_centers, key=lambda b: b[0][0])  # Sort by x1
        
        # Find actual gaps between consecutive boxes
        gaps = []
        min_gap_size = 80  # Minimum actual gap size to consider a column boundary (pixels)
        
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
