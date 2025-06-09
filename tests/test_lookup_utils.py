import unittest
from unittest.mock import patch, MagicMock
import xml.etree.ElementTree as ET

from libs.utils.lookup_utils import search_openlibrary, search_dnb, lookup_book_details

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

if __name__ == '__main__':
    unittest.main()