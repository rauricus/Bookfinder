import unittest
from libs.utils.lookup_utils import search_openlibrary, search_lobid_gnd_work, search_dnb

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

    def test_openlibrary_nonexistent(self):
        result = search_openlibrary("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)

    def test_lobid_query(self):
        result = search_lobid_gnd_work("Der Steppenwolf")
        self.assertIsNotNone(result)
        self.assertIn("Der Steppenwolf", result["title"])
        self.assertIn("Hesse, Hermann", result["author"])
        self.assertIn("Q217073", result["wikidata"])
        print("lobid gnd:", result)

    def test_lobid_nonexistent(self):
        result = search_lobid_gnd_work("asldkfjasldkfj-nichtvorhanden")
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()