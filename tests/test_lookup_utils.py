import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from libs.utils.lookup_utils import search_openlibrary, search_dnb, search_lobid_gnd_work, lookup_book_details, search_google_books

class TestLookupUtils(unittest.TestCase):
    @patch('libs.utils.lookup_utils.requests.get')
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

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_openlibrary_no_result(self, mock_get):
        # Simuliere, dass die API keine Treffer liefert
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {"docs": []}
        mock_get.return_value = fake_response

        result = search_openlibrary("Nichtexistent", language="de")
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_dnb_success(self, mock_get):
        # Simuliere eine erfolgreiche Antwort der DNB-API mit XML-Inhalt
        fake_xml = '''
        <searchRetrieveResponse xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:gndo="https://d-nb.info/standards/elementset/gnd#">
            <records>
                <record>
                    <recordData>
                        <dc:title>Testbuch DNB</dc:title>
                        <dcterms:creator>
                            <gndo:preferredName>Autor DNB</gndo:preferredName>
                        </dcterms:creator>
                        <dcterms:issued>2019</dcterms:issued>
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

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_swisscovery_offline(self, mock_get):
        # Simuliere eine typische SRU-XML-Antwort von swisscovery
        fake_xml = '''
        <searchRetrieveResponse xmlns:marc="http://www.loc.gov/MARC21/slim">
            <records>
                <record>
                    <recordData>
                        <marc:record>
                            <marc:datafield tag="245">
                                <marc:subfield code="a">Testbuch Swisscovery</marc:subfield>
                            </marc:datafield>
                            <marc:datafield tag="100">
                                <marc:subfield code="a">Autor Swisscovery</marc:subfield>
                            </marc:datafield>
                            <marc:datafield tag="264">
                                <marc:subfield code="c">2022</marc:subfield>
                            </marc:datafield>
                            <marc:datafield tag="020">
                                <marc:subfield code="a">978-3-16-148410-0</marc:subfield>
                            </marc:datafield>
                        </marc:record>
                    </recordData>
                </record>
            </records>
        </searchRetrieveResponse>
        '''
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content = fake_xml.encode('utf-8')
        fake_response.text = fake_xml
        mock_get.return_value = fake_response
        from libs.utils.lookup_utils import search_swisscovery
        result = search_swisscovery("Testbuch Swisscovery")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Testbuch Swisscovery")
        self.assertEqual(result["authors"], "Autor Swisscovery")
        self.assertEqual(result["year"], "2022")
        self.assertEqual(result["isbn"], "9783161484100")

    def test_search_swisscovery_live(self):
        # Live-Test: Fragt swisscovery wirklich ab
        from libs.utils.lookup_utils import search_swisscovery
        result = search_swisscovery("Der Steppenwolf")
        if result is None:
            self.skipTest("swisscovery nicht erreichbar oder kein Treffer.")
        else:
            self.assertIn("Steppenwolf", result["title"])
            # Jahr und ISBN sind optional, aber falls vorhanden, prüfen wir das Format
            if result["year"]:
                self.assertRegex(result["year"], r"\d{4}")
            if result["isbn"]:
                self.assertRegex(result["isbn"], r"^97[89]\d{10}$|^\d{9}[\dX]$")

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_lobid_gnd_success(self, mock_get):
        """Test successful lobid GND search with valid response"""
        mock_response_data = {
            "member": [
                {
                    "preferredName": "Der Steppenwolf",
                    "firstAuthor": [{"label": "Hesse, Hermann"}],
                    "dateOfPublication": ["1927"]
                }
            ]
        }
        
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = mock_response_data
        mock_get.return_value = fake_response
        
        result = search_lobid_gnd_work("Der Steppenwolf")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Der Steppenwolf")
        self.assertEqual(result["authors"], "Hesse, Hermann")
        self.assertEqual(result["year"], "1927")
        self.assertIsNone(result["isbn"])

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_lobid_gnd_with_acceptable_authors(self, mock_get):
        """Test lobid GND search with author filtering"""
        mock_response_data = {
            "member": [
                {
                    "preferredName": "Der Steppenwolf",
                    "firstAuthor": [{"label": "Anderer Autor"}]
                },
                {
                    "preferredName": "Der Steppenwolf",
                    "firstAuthor": [{"label": "Hesse, Hermann"}],
                    "dateOfPublication": ["1927"]
                }
            ]
        }
        
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = mock_response_data
        mock_get.return_value = fake_response
        
        result = search_lobid_gnd_work("Der Steppenwolf", acceptable_authors=["Hesse"])
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Der Steppenwolf")
        self.assertIn("Hesse", result["authors"])

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_lobid_gnd_no_results(self, mock_get):
        """Test lobid GND search with no results"""
        mock_response_data = {"member": []}
        
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = mock_response_data
        mock_get.return_value = fake_response
        
        result = search_lobid_gnd_work("Nonexistent Book")
        self.assertIsNone(result)

    def test_search_lobid_gnd_empty_query(self):
        """Test that empty query returns None"""
        result = search_lobid_gnd_work("")
        self.assertIsNone(result)
        
        result = search_lobid_gnd_work(None)
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_google_books_success(self, mock_get):
        # Simuliere eine erfolgreiche Antwort der Google Books API
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {
            "items": [
                {
                    "volumeInfo": {
                        "title": "Testbuch Google",
                        "authors": ["Autor Google", "Co-Autor"],
                        "publishedDate": "2021-05-15",
                        "industryIdentifiers": [
                            {
                                "type": "ISBN_13",
                                "identifier": "978-3-16-148410-0"
                            }
                        ]
                    }
                }
            ]
        }
        mock_get.return_value = fake_response
        
        result = search_google_books("Testbuch Google", language="de")
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Testbuch Google")
        self.assertEqual(result["authors"], "Autor Google, Co-Autor")
        self.assertEqual(result["year"], "2021")
        self.assertEqual(result["isbn"], "9783161484100")

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_google_books_no_result(self, mock_get):
        # Simuliere, dass die API keine Treffer liefert
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {"items": []}
        mock_get.return_value = fake_response

        result = search_google_books("Nichtexistent", language="de")
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_google_books_no_items(self, mock_get):
        # Simuliere eine Antwort ohne "items" key
        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.json.return_value = {"totalItems": 0}
        mock_get.return_value = fake_response

        result = search_google_books("Nichtexistent", language="de")
        self.assertIsNone(result)

    def test_search_google_books_empty_query(self):
        """Test that empty query returns None"""
        result = search_google_books("")
        self.assertIsNone(result)
        
        result = search_google_books(None)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()