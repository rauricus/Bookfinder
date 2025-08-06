#!/usr/bin/env python3
"""
Tests for the clean_ocr_text function in text_utils.py

This test file validates the improved OCR text cleaning functionality,
specifically testing:
1. Replacement of special characters with spaces (instead of removal)
2. Preservation of numbers in various contexts
3. Proper space normalization
"""

import os
import sys
import unittest

# Add the parent directory to sys.path to import libs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.utils.text_utils import clean_ocr_text


class TestCleanOcrText(unittest.TestCase):
    
    def test_basic_text_cleaning(self):
        """Test basic text cleaning functionality."""
        # Simple text should be preserved and lowercased
        result = clean_ocr_text("Hello World")
        self.assertEqual(result, "hello world")
        
        # German umlauts should be preserved
        result = clean_ocr_text("Bücher und Märchen")
        self.assertEqual(result, "bücher und märchen")
    
    def test_special_characters_replaced_with_spaces(self):
        """Test that special characters are replaced with spaces, not removed."""
        # Punctuation should be replaced with spaces when standalone
        result = clean_ocr_text("Hello,World!")
        self.assertEqual(result, "hello world")
        
        # Multiple special characters should create proper spacing
        result = clean_ocr_text("Text@#$%with&*special()chars")
        self.assertEqual(result, "text with special chars")
        
        # Mixed punctuation and spaces - standalone punctuation removed
        result = clean_ocr_text("Word1 , Word2 ; Word3 : Word4 .")
        self.assertEqual(result, "word1 word2 word3 word4")
    
    def test_punctuation_preservation_in_words(self):
        """Test that punctuation is preserved when part of words but removed when standalone."""
        # Punctuation within words should be preserved
        result = clean_ocr_text("Klasse 8/9")
        self.assertEqual(result, "klasse 8/9")
        
        # Multiple punctuation types in words
        result = clean_ocr_text("Version 2.1: Das neue Update")
        self.assertEqual(result, "version 2.1: das neue update")
        
        # ISBN-like format should be preserved
        result = clean_ocr_text("978-3-123-45678")
        self.assertEqual(result, "978-3-123-45678")
        
        # Standalone punctuation should be removed
        result = clean_ocr_text("Wort . Anderes - Wort")
        self.assertEqual(result, "wort anderes wort")
        
        # Mixed: some preserved, some removed
        result = clean_ocr_text("Text1/2 . Text3:4")
        self.assertEqual(result, "text1/2 text3:4")
    
    def test_numbers_preservation(self):
        """Test that numbers are preserved in various contexts."""
        # Standalone numbers should be preserved
        result = clean_ocr_text("Published in 2022")
        self.assertEqual(result, "published in 2022")
        
        # Numbers as part of words should be preserved
        result = clean_ocr_text("2nd Edition")
        self.assertEqual(result, "2nd edition")
        
        # ISBN-like numbers with dashes should be preserved, colon kept when meaningful
        result = clean_ocr_text("ISBN: 978-3-123-45678-9")
        self.assertEqual(result, "isbn: 978-3-123-45678-9")
        
        # Years with dash ranges should work
        result = clean_ocr_text("Der große Krieg 1914-1918")
        self.assertEqual(result, "der große krieg 1914-1918")
    
    def test_multiple_spaces_normalization(self):
        """Test that multiple spaces are normalized to single spaces."""
        # Multiple spaces should become single space
        result = clean_ocr_text("Word1    Word2")
        self.assertEqual(result, "word1 word2")
        
        # Tabs and other whitespace should be normalized
        result = clean_ocr_text("Word1\t\n   Word2")
        self.assertEqual(result, "word1 word2")
        
        # Leading and trailing spaces should be stripped
        result = clean_ocr_text("  Text with spaces  ")
        self.assertEqual(result, "text with spaces")
    
    def test_unicode_normalization(self):
        """Test Unicode normalization and character handling."""
        # Different Unicode representations should be normalized
        result = clean_ocr_text("café")  # Normal é
        expected = "café"
        self.assertEqual(result, expected)
        
        # Mixed language characters
        result = clean_ocr_text("Français & Deutsch")
        self.assertEqual(result, "français deutsch")
    
    def test_real_world_ocr_examples(self):
        """Test with realistic OCR output examples."""
        # Common OCR artifacts with punctuation - trademark symbol removed, multiple dots kept if adjacent
        result = clean_ocr_text("Harry Potter™ & der Stein...")
        self.assertEqual(result, "harry potter der stein..")
        
        # Title with author and year - preserve punctuation in context
        result = clean_ocr_text("Die Buddenbrooks (1901) - Thomas Mann")
        self.assertEqual(result, "die buddenbrooks 1901 thomas mann")
        
        # Publisher info that should be cleaned
        result = clean_ocr_text("Rowohlt Verlag® 2023")
        self.assertEqual(result, "rowohlt verlag 2023")
        
        # Mixed punctuation in titles - colon preserved when part of title
        result = clean_ocr_text("Der Herr der Ringe: Die Gefährten")
        self.assertEqual(result, "der herr der ringe: die gefährten")
    
    def test_empty_and_edge_cases(self):
        """Test edge cases and empty inputs."""
        # Empty string
        result = clean_ocr_text("")
        self.assertEqual(result, "")
        
        # Only whitespace
        result = clean_ocr_text("   \t\n   ")
        self.assertEqual(result, "")
        
        # Only special characters
        result = clean_ocr_text("!@#$%^&*()")
        self.assertEqual(result, "")
        
        # Only numbers
        result = clean_ocr_text("123456")
        self.assertEqual(result, "123456")
    
    def test_language_specific_characters(self):
        """Test that language-specific characters are properly handled."""
        # German characters should be preserved
        result = clean_ocr_text("Größe und Wärme", languages=("de",))
        self.assertEqual(result, "größe und wärme")
        
        # French characters should be preserved when French is included
        result = clean_ocr_text("Café français", languages=("de", "fr"))
        self.assertEqual(result, "café français")
        
        # Characters not in specified languages should be replaced
        result = clean_ocr_text("Hello Wörld", languages=("de",))  # 'o' should be preserved, but let's test real edge cases
        self.assertEqual(result, "hello wörld")  # Both German and basic Latin should work
    
    def test_mixed_content_scenarios(self):
        """Test complex scenarios with mixed content types."""
        # Book spine with multiple elements - preserve meaningful punctuation
        ocr_input = "J.K. Rowling | Harry Potter & der Stein der Weisen (1997) | Carlsen®"
        expected = "j.k. rowling harry potter der stein der weisen 1997 carlsen"
        result = clean_ocr_text(ocr_input)
        self.assertEqual(result, expected)
        
        # Scientific title with numbers and symbols - preserve meaningful punctuation  
        ocr_input = "Mathematik für Klasse 8/9 - Algebra & Geometrie (2. Auflage)"
        expected = "mathematik für klasse 8/9 algebra geometrie 2. auflage"
        result = clean_ocr_text(ocr_input)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
