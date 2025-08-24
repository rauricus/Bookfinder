import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import from libs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from libs.utils.lookup_utils import search_worldcat


class TestWorldCatLookup(unittest.TestCase):
    """Test cases for WorldCat book lookup functionality"""

    def test_search_worldcat_empty_query(self):
        """Test that empty query returns None"""
        result = search_worldcat("")
        self.assertIsNone(result)

        result = search_worldcat(None)
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_successful(self, mock_get):
        """Test successful WorldCat search with valid response"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>1</numberOfRecords>
    <records>
        <record>
            <recordData>
                <record xmlns="http://www.loc.gov/MARC21/slim">
                    <datafield tag="245" ind1="1" ind2="0">
                        <subfield code="a">Der Herr der Ringe</subfield>
                        <subfield code="c">J.R.R. Tolkien</subfield>
                    </datafield>
                    <datafield tag="100" ind1="1" ind2=" ">
                        <subfield code="a">Tolkien, J. R. R.</subfield>
                    </datafield>
                    <datafield tag="264" ind1=" " ind2="1">
                        <subfield code="c">1954</subfield>
                    </datafield>
                    <datafield tag="020" ind1=" " ind2=" ">
                        <subfield code="a">9783608938047</subfield>
                    </datafield>
                </record>
            </recordData>
        </record>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Der Herr der Ringe")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Der Herr der Ringe")
        self.assertEqual(result["authors"], "Tolkien, J. R. R.")
        self.assertEqual(result["year"], "1954")
        self.assertEqual(result["isbn"], "9783608938047")
        self.assertIn("_raw_response", result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_no_results(self, mock_get):
        """Test WorldCat search with no results"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>0</numberOfRecords>
    <records>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Nonexistent Book Title")
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_diagnostic_error(self, mock_get):
        """Test WorldCat search with SRU diagnostic error"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <diagnostics xmlns="http://www.loc.gov/zing/srw/diagnostic/">
        <diagnostic>
            <uri>info:srw/diagnostic/1/4</uri>
            <message>Unsupported operation</message>
        </diagnostic>
    </diagnostics>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Test Query")
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_multiple_authors(self, mock_get):
        """Test WorldCat search with multiple authors"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>1</numberOfRecords>
    <records>
        <record>
            <recordData>
                <record xmlns="http://www.loc.gov/MARC21/slim">
                    <datafield tag="245" ind1="1" ind2="0">
                        <subfield code="a">Programmieren lernen mit Python:</subfield>
                    </datafield>
                    <datafield tag="100" ind1="1" ind2=" ">
                        <subfield code="a">Downey, Allen B.,</subfield>
                    </datafield>
                    <datafield tag="700" ind1="1" ind2=" ">
                        <subfield code="a">Müller, Thomas,</subfield>
                    </datafield>
                    <datafield tag="700" ind1="1" ind2=" ">
                        <subfield code="a">Schmidt, Peter,</subfield>
                    </datafield>
                    <datafield tag="260" ind1=" " ind2=" ">
                        <subfield code="c">2018</subfield>
                    </datafield>
                    <datafield tag="020" ind1=" " ind2=" ">
                        <subfield code="a">978-3-96009-076-7</subfield>
                    </datafield>
                </record>
            </recordData>
        </record>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Programmieren lernen mit Python")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Programmieren lernen mit Python")
        self.assertIn("Downey, Allen B.", result["authors"])
        self.assertIn("Müller, Thomas", result["authors"])
        self.assertIn("Schmidt, Peter", result["authors"])
        self.assertEqual(result["year"], "2018")
        self.assertEqual(result["isbn"], "9783960090767")

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_minimal_data(self, mock_get):
        """Test WorldCat search with minimal book data"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>1</numberOfRecords>
    <records>
        <record>
            <recordData>
                <record xmlns="http://www.loc.gov/MARC21/slim">
                    <datafield tag="245" ind1="1" ind2="0">
                        <subfield code="a">Minimal Book</subfield>
                    </datafield>
                </record>
            </recordData>
        </record>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Minimal Book")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["title"], "Minimal Book")
        self.assertIsNone(result["authors"])
        self.assertIsNone(result["year"])
        self.assertIsNone(result["isbn"])

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_network_error(self, mock_get):
        """Test WorldCat search with network error"""
        mock_get.side_effect = Exception("Network error")

        result = search_worldcat("Test Book")
        self.assertIsNone(result)

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_isbn_cleaning(self, mock_get):
        """Test ISBN cleaning in WorldCat response"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>1</numberOfRecords>
    <records>
        <record>
            <recordData>
                <record xmlns="http://www.loc.gov/MARC21/slim">
                    <datafield tag="245" ind1="1" ind2="0">
                        <subfield code="a">Test Book</subfield>
                    </datafield>
                    <datafield tag="020" ind1=" " ind2=" ">
                        <subfield code="a">978-3-16-148410-0 (hardcover)</subfield>
                    </datafield>
                </record>
            </recordData>
        </record>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Test Book")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["isbn"], "9783161484100")

    @patch('libs.utils.lookup_utils.requests.get')
    def test_search_worldcat_year_extraction(self, mock_get):
        """Test year extraction from various date formats"""
        mock_response = '''<?xml version="1.0" encoding="UTF-8"?>
<searchRetrieveResponse xmlns="http://www.loc.gov/zing/srw/">
    <numberOfRecords>1</numberOfRecords>
    <records>
        <record>
            <recordData>
                <record xmlns="http://www.loc.gov/MARC21/slim">
                    <datafield tag="245" ind1="1" ind2="0">
                        <subfield code="a">Test Book</subfield>
                    </datafield>
                    <datafield tag="264" ind1=" " ind2="1">
                        <subfield code="c">[2021]</subfield>
                    </datafield>
                </record>
            </recordData>
        </record>
    </records>
</searchRetrieveResponse>'''

        fake_response = MagicMock()
        fake_response.raise_for_status = lambda: None
        fake_response.content.decode.return_value = mock_response
        mock_get.return_value = fake_response

        result = search_worldcat("Test Book")
        
        self.assertIsNotNone(result)
        self.assertEqual(result["year"], "2021")


if __name__ == "__main__":
    unittest.main()
