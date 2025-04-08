import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

from libs.lookup_utils import search_openlibrary, search_dnb, lookup_book_details

class TestLookupUtils(unittest.TestCase):
    @patch('libs.lookup_utils.requests.get')
    def test_search_openlibrary_success(self, mock_get):
        # Simuliere eine erfolgreiche Antwort der OpenLibrary-API
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {
            "docs": [
                {
                    "title": "Testbuch",
                    "author_name": ["Autor A"],
                    "first_publish_year": 2020,
                    "isbn": ["1234567890"]
                }
            ]
        }
        mock_get.return_value = fake_response
        
        result = search_openlibrary("Testbuch", language="de")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Testbuch")
        self.assertEqual(result["authors"], "Autor A")
        self.assertEqual(result["year"], 2020)
        self.assertEqual(result["isbn"], "1234567890")

    @patch('libs.lookup_utils.requests.get')
    def test_search_openlibrary_no_result(self, mock_get):
        # Simuliere, dass die API keine Treffer liefert
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {"docs": []}
        mock_get.return_value = fake_response

        result = search_openlibrary("Nichtexistent", language="de")
        self.assertIsNone(result)

    @patch('libs.lookup_utils.requests.get')
    def test_search_dnb_success(self, mock_get):
        # Simuliere eine erfolgreiche Antwort der DNB-API mit XML-Inhalt
        fake_xml = '''
        <searchRetrieveResponse xmlns:dc="http://purl.org/dc/elements/1.1/">
            <records>
                <record>
                    <recordData>
                        <dc:title>Testbuch DNB</dc:title>
                        <dc:creator>Autor DNB</dc:creator>
                        <dc:date>2019</dc:date>
                    </recordData>
                </record>
            </records>
        </searchRetrieveResponse>
        '''
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content = fake_xml.encode('utf-8')
        mock_get.return_value = fake_response

        result = search_dnb("Testbuch DNB")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Testbuch DNB")
        self.assertEqual(result["authors"], "Autor DNB")
        self.assertEqual(result["year"], "2019")

    @patch('libs.lookup_utils.search_dnb')
    @patch('libs.lookup_utils.search_openlibrary')
    def test_lookup_book_details_prefer_dnb(self, mock_openlibrary, mock_dnb):
        # Wenn DNB ein Ergebnis liefert, soll OpenLibrary nicht aufgerufen werden
        mock_dnb.return_value = {"title": "DNB Buch", "authors": "DNB Autor", "year": "2020", "isbn": "Unbekannt"}
        result = lookup_book_details("Irgendein Buch", language="de")
        self.assertEqual(result["title"], "DNB Buch")
        mock_openlibrary.assert_not_called()

    @patch('libs.lookup_utils.search_dnb')
    @patch('libs.lookup_utils.search_openlibrary')
    def test_lookup_book_details_fallback_to_openlibrary(self, mock_openlibrary, mock_dnb):
        # Wenn DNB kein Ergebnis liefert, soll als Fallback OpenLibrary genutzt werden
        mock_dnb.return_value = None
        mock_openlibrary.return_value = {"title": "OpenLibrary Buch", "authors": "OL Autor", "year": "2021", "isbn": "Unbekannt"}
        result = lookup_book_details("Irgendein Buch", language="de")
        self.assertEqual(result["title"], "OpenLibrary Buch")

if __name__ == '__main__':
    unittest.main()