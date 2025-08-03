"""
Tests for text region sorting functionality.

This module contains comprehensive tests for the TextRegionSorter class
to ensure proper sorting of text regions on book spines.
"""

import unittest
import sys
import os

from libs.utils.text_classification import TextRegionSorter

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestTextRegionSorting(unittest.TestCase):
    """Test cases for TextRegionSorter functionality."""
    
    def test_basic_vertical_sorting(self):
        """Test basic top-to-bottom sorting."""
        boxes = [
            (10, 80, 110, 100),   # Bottom box
            (10, 10, 100, 30),    # Top box
            (10, 40, 120, 60)     # Middle box
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should be sorted by Y position: top, middle, bottom
        expected_y_order = [10, 40, 80]  # y1 coordinates
        actual_y_order = [box[1] for box in sorted_boxes]
        
        self.assertEqual(actual_y_order, expected_y_order,
                        "Basic vertical sorting should work correctly")
    
    def test_horizontal_sorting_same_row(self):
        """Test left-to-right sorting for boxes on the same horizontal line."""
        boxes = [
            (100, 10, 150, 30),   # Right box
            (10, 10, 60, 30),     # Left box
            (70, 10, 120, 30)     # Middle box
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should be sorted by X position: left, middle, right
        expected_x_order = [10, 70, 100]  # x1 coordinates
        actual_x_order = [box[0] for box in sorted_boxes]
        
        self.assertEqual(actual_x_order, expected_x_order,
                        "Horizontal sorting should work left-to-right")
    
    def test_out_of_order_regions(self):
        """Test sorting when boxes are provided in mixed order."""
        boxes = [
            (10, 80, 110, 100),   # Bottom box (should be last)
            (10, 10, 100, 30),    # Top box (should be first)
            (10, 40, 120, 60)     # Middle box (should be middle)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should be sorted by Y position: top, middle, bottom
        expected_y_order = [10, 40, 80]  # y1 coordinates
        actual_y_order = [box[1] for box in sorted_boxes]
        
        self.assertEqual(actual_y_order, expected_y_order,
                        "Should sort by actual position, not input order")
    
    def test_horizontally_close_grouping(self):
        """Test that horizontally close boxes are grouped in the same row."""
        boxes = [
            (10, 10, 80, 30),      # Left box (top row)
            (85, 10, 140, 30),     # Right box (top row, close - gap=5px)
            (50, 40, 110, 60),     # Bottom box (separate row)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should maintain the top row order: left, right, then bottom
        expected_positions = [(10, 10), (85, 10), (50, 40)]  # (x1, y1) coordinates
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Horizontally close boxes should be grouped correctly")
    
    def test_horizontally_distant_separation(self):
        """Test that horizontally distant boxes create separate columns."""
        boxes = [
            (10, 10, 60, 30),     # Left column
            (200, 10, 250, 30),   # Right column (gap=140px > 80px min_gap_size)
            (10, 50, 100, 70)     # Left column, below first box
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected: Left column (top, then bottom), then Right column
        expected_positions = [(10, 10), (10, 50), (200, 10)]  # (x1, y1) coordinates
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Horizontally distant boxes should create separate columns")
    
    def test_complex_multi_row_scenario(self):
        """Test complex scenario with multiple rows and different horizontal distances."""
        boxes = [
            (10, 10, 80, 30),      # Top left
            (85, 10, 140, 30),     # Top right (close - gap=5px)
            (50, 40, 110, 60),     # Middle (centered)
            (10, 70, 70, 90),      # Bottom left
            (200, 70, 280, 90)     # Bottom right (far - gap=130px)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected order: top row (left, right), middle, bottom row (left, right)
        expected_positions = [(10, 10), (85, 10), (50, 40), (10, 70), (200, 70)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Complex multi-row scenario should be handled correctly")
    
    def test_horizontal_distance_threshold(self):
        """Test that the gap analysis (80px min_gap_size) works correctly."""
        boxes = [
            (10, 10, 50, 30),     # Left column
            (60, 10, 100, 30),    # Left column (gap=10px < 80px min_gap_size)
            (300, 10, 340, 30),   # Right column (gap=200px > 80px min_gap_size)
            (50, 50, 100, 70)     # Left column, below
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected: Left column (Left, Middle, Below), then Right column
        expected_positions = [(10, 10), (60, 10), (50, 50), (300, 10)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "80px gap threshold should group Left+Middle in same column, separate Right")
    
    def test_empty_input(self):
        """Test handling of empty input."""
        boxes = []
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        self.assertEqual(sorted_boxes, [],
                        "Empty input should return empty result")
    
    def test_single_region(self):
        """Test handling of single bounding box."""
        boxes = [(10, 10, 100, 30)]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        expected_boxes = [(10, 10, 100, 30)]
        
        self.assertEqual(sorted_boxes, expected_boxes,
                        "Single box should be handled correctly")
    
    def test_overlapping_regions(self):
        """Test handling of overlapping bounding boxes."""
        boxes = [
            (10, 10, 60, 30),     # Left box
            (40, 10, 90, 30)      # Right box (overlaps with left box)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should still sort by center position (left box has lower center_x)
        expected_positions = [(10, 10), (40, 10)]  # (x1, y1) coordinates
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Overlapping boxes should be sorted by center position")

    def test_three_column_layout(self):
        """Test three-column layout like 'GOLDMANN | ALLEN CARR | 43388'."""
        boxes = [
            (10, 20, 80, 40),     # Left column: "GOLDMANN" 
            (120, 10, 200, 30),   # Center column: "ALLEN CARR" (top)
            (120, 35, 180, 55),   # Center column: "Endlich Nichtraucher!" (bottom)
            (250, 20, 290, 40)    # Right column: "43388"
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected: Left column, Center column (top-to-bottom), Right column
        expected_positions = [(10, 20), (120, 10), (120, 35), (250, 20)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Three-column layout should be sorted correctly")

    def test_author_title_layout(self):
        """Test typical author-title layout like 'Christoffer Carlsson | UNTER DEM STURM'."""
        boxes = [
            (10, 10, 90, 30),     # Left column: "Christoffer" (top)
            (10, 35, 70, 55),     # Left column: "Carlsson" (bottom)
            (150, 10, 220, 30),   # Right column: "UNTER DEM" (top)
            (150, 35, 200, 55),   # Right column: "STURM" (bottom)
            (150, 60, 180, 80)    # Right column: "666" (bottom)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected: Left column (author), then Right column (title+number)
        expected_positions = [(10, 10), (10, 35), (150, 10), (150, 35), (150, 60)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Author-title layout should preserve column grouping")

    def test_single_line_title(self):
        """Test single line titles like 'PICASSO' or 'WILLI REICH • JOSEPH HAYDN'."""
        boxes = [
            (50, 20, 120, 40),    # Single title in center
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        expected_boxes = [(50, 20, 120, 40)]
        self.assertEqual(sorted_boxes, expected_boxes,
                        "Single line titles should be handled correctly")

    def test_vertical_text_stack(self):
        """Test vertically stacked text within one column."""
        boxes = [
            (10, 10, 80, 25),     # Line 1
            (10, 30, 80, 45),     # Line 2
            (10, 50, 80, 65),     # Line 3
            (10, 70, 80, 85),     # Line 4
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Should maintain top-to-bottom order within single column
        expected_y_order = [10, 30, 50, 70]
        actual_y_order = [box[1] for box in sorted_boxes]
        
        self.assertEqual(actual_y_order, expected_y_order,
                        "Vertical text stack should maintain order")

    def test_minimal_gap_edge_case(self):
        """Test edge case around the 80px gap threshold."""
        boxes = [
            (10, 20, 50, 40),     # Left
            (130, 20, 170, 40),   # Center (gap=80px - exactly at threshold)
            (250, 20, 290, 40)    # Right (gap=80px - exactly at threshold)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # With gap exactly at 80px, should create separate columns
        expected_positions = [(10, 20), (130, 20), (250, 20)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "80px gap threshold edge case should be handled correctly")

    def test_uneven_column_heights(self):
        """Test columns with different heights (common in book spines)."""
        boxes = [
            (10, 10, 80, 30),     # Left column: single line
            (150, 5, 220, 25),    # Right column: line 1
            (150, 30, 200, 50),   # Right column: line 2  
            (150, 55, 180, 75),   # Right column: line 3
            (150, 80, 210, 100)   # Right column: line 4
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # Expected: Left column (1 item), then Right column (4 items top-to-bottom)
        expected_positions = [(10, 10), (150, 5), (150, 30), (150, 55), (150, 80)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Uneven column heights should be handled correctly")

    def test_very_small_gaps(self):
        """Test that very small gaps don't create unnecessary columns."""
        boxes = [
            (10, 20, 50, 40),     # Word 1
            (55, 20, 95, 40),     # Word 2 (gap=5px - should stay in same column)
            (100, 20, 140, 40),   # Word 3 (gap=5px - should stay in same column)
        ]
        
        sorted_boxes = TextRegionSorter.sort_boxes_by_position(boxes)
        
        # All should be in one column, sorted left-to-right within same row
        expected_positions = [(10, 20), (55, 20), (100, 20)]
        actual_positions = [(box[0], box[1]) for box in sorted_boxes]
        
        self.assertEqual(actual_positions, expected_positions,
                        "Small gaps should not create separate columns")


def run_all_tests():
    """Run all text region sorting tests."""
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTextRegionSorting)
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return True if all tests passed
    return result.wasSuccessful()


if __name__ == '__main__':
    print("Running Text Region Sorting Tests...")
    print("=" * 50)
    
    success = run_all_tests()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
