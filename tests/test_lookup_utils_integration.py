import unittest
from libs.lookup_utils import search_openlibrary, search_lobid_gnd_work

class TestLookupUtilsIntegration(unittest.TestCase):

    def test_openlibrary_real_query(self):
        result = search_openlibrary("Der Steppenwolf", language="de")
        self.assertIsNotNone(result)
        self.assertIn("Steppenwolf", result["title"])
        print("OpenLibrary:", result)

    def test_openlibrary_nonexistent(self):
        result = search_openlibrary("asldkfjasldkfj-nichtvorhanden", language="de")
        self.assertIsNone(result)

    def test_lobid_real_query(self):
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