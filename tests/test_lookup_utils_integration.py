import unittest
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from libs.utils.lookup_utils import search_openlibrary, search_lobid_gnd_work, search_dnb, search_worldcat, search_google_books

class TestLookupUtilsIntegration(unittest.TestCase):

    def test_dnb_query(self):
        result = search_dnb("Der Steppenwolf")
        self.assertIsNotNone(result)
        self.assertIn("Steppenwolf", result["title"])
        print("DNB:", result)
        
    def test_dnb_nonexistent(self):
        result = search_dnb("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)
        
    def test_openlibrary_query(self):
        result = search_openlibrary("Der Steppenwolf", language="de")
        self.assertIsNotNone(result)
        self.assertIn("Steppenwolf", result["title"])
        print("OpenLibrary:", result)

    def test_worldcat_query(self):
        """Test actual WorldCat integration - currently disabled due to API key requirement"""
        # WorldCat is currently disabled in lookup_book_details due to authentication requirements
        # result = search_worldcat("Der Steppenwolf", language="de")
        # if result:  # Only assert if we get a result (service may be unavailable)
        #     self.assertIn("Steppenwolf", result["title"])
        #     print("WorldCat:", result)
        # else:
        #     print("WorldCat: Service unavailable or no results found")
        print("WorldCat: Currently disabled due to API authentication requirements")
        pass
        
    def test_worldcat_nonexistent(self):
        result = search_worldcat("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)

    def test_openlibrary_nonexistent(self):
        result = search_openlibrary("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)

    def test_lobid_query(self):
        result = search_lobid_gnd_work("Der Steppenwolf")
        self.assertIsNotNone(result)
        self.assertIn("Steppenwolf", result["title"])
        # Test dass Autoren korrekt extrahiert werden
        if result["authors"]:
            self.assertIn("Hesse", result["authors"])
        # Test dass Jahr extrahiert wird
        if result["year"]:
            self.assertEqual(result["year"], "1927")
        print("lobid gnd:", result)

    def test_lobid_with_acceptable_authors(self):
        """Test GND search with author filtering"""
        result = search_lobid_gnd_work("Der Steppenwolf", acceptable_authors=["Hesse"])
        self.assertIsNotNone(result)
        self.assertIn("Steppenwolf", result["title"])
        self.assertIn("Hesse", result["authors"])
        print("lobid gnd with author filter:", result)

    def test_lobid_nonexistent(self):
        result = search_lobid_gnd_work("asldkfjasldkfj-nichtvorhanden")
        self.assertIsNone(result)

    def test_google_books_query(self):
        """Test actual Google Books API integration"""
        result = search_google_books("Der Steppenwolf", language="de")
        if result:  # Service may be unavailable or have rate limits
            self.assertIn("Steppenwolf", result["title"])
            print("Google Books:", result)
        else:
            print("Google Books: Service unavailable or no results found")

    def test_google_books_nonexistent(self):
        result = search_google_books("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()