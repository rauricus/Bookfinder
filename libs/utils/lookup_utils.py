import re

import requests
import xml.etree.ElementTree as ET
import json
import urllib.parse

from libs.utils.general_utils import iso639_1_to_3
from libs.logging import get_logger


# Module-specific logger that uses the module name as prefix for log messages
logger = get_logger(__name__)

def initialize():
    # Add any necessary initialization code here
    pass

    
def search_dnb(query_string, language="de"):
    if not query_string:
        logger.info("No title provided. Skipping DNB lookup.")
        return None

    logger.info("🔎 Searching with DNB (SRU)...")

    try:
        dnb_url = "https://services.dnb.de/sru/dnb"
        dnb_params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": f'{query_string} and spr="{iso639_1_to_3(language)}"',
            "maximumRecords": 1
        }
        dnb_response = requests.get(dnb_url, params=dnb_params, timeout=10)
        dnb_response.raise_for_status()
        
        # Store the raw XML response as string
        raw_response = dnb_response.content.decode('utf-8')
        
        root = ET.fromstring(dnb_response.content)
        ns = {
            'dc': 'http://purl.org/dc/elements/1.1/',
            'dcterms': 'http://purl.org/dc/terms/',
            'gndo': 'https://d-nb.info/standards/elementset/gnd#',
            'bibo': 'http://purl.org/ontology/bibo/'
        }

        title_el = root.find('.//dc:title', ns)
        author_el = root.find('.//dcterms:creator//gndo:preferredName', ns)
        year_el = root.find('.//dcterms:issued', ns)
        isbn_el = root.find('.//bibo:isbn13', ns)

        if all(el is None for el in [title_el, author_el, year_el, isbn_el]):
            logger.info(f"⚠️ No book found for query: {query_string}")
            return None

        result = {
            "title": title_el.text if title_el is not None else None,
            "authors": author_el.text if author_el is not None else None,
            "year": year_el.text if year_el is not None else None,
            "isbn": isbn_el.text if isbn_el is not None else None,
            "_raw_response": raw_response  # Include raw response
        }
        
        return result

    except Exception as e:
        logger.error(f"❌ Error in DNB request: {e}")
        return None
    
    
def search_openlibrary(query_string, language="de"):
    """
    Searches for book details based on the title in the OpenLibrary API.
    
    OpenLibrary API: https://openlibrary.org/developers/api

    Args:
        query_string (str): The string with title, author, etc. of the book to search for.
        language (str): The language of the book (default: "de").
    
    Returns:
        dict: A dictionary with book details (title, authors, year, ISBN) or None if no book was found.
    """

    if not query_string:  # Check if the title is empty or None
        logger.info("No title provided. Skipping OpenLibrary lookup.")
        return None
    
    logger.info("🔎 Searching with OpenLibrary...")

    base_url = "https://openlibrary.org/search.json"
    params = {
        "q": query_string,
        "lang": language,
        "limit": 1  # Return only the most relevant result
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Raise error for HTTP status codes
        data = response.json()

        if "docs" in data and len(data["docs"]) > 0:
            book = data["docs"][0]  # Take the first result
            
            # Store the raw JSON response
            raw_response = json.dumps(data, ensure_ascii=False)  # Preserve UTF-8 characters
            
            result = {
                "title": book.get("title"),
                "authors": ", ".join(book.get("author_name", [])) if book.get("author_name") else None,
                "year": book.get("first_publish_year"),
                "isbn": book.get("isbn")[0] if "isbn" in book and book.get("isbn") else None,
                "_raw_response": raw_response  # Include raw response
            }
            return result
        else:
            logger.info(f"⚠️ No book found for query: {query_string}")
            return None

    except requests.RequestException as e:
        logger.error(f"❌ Error in OpenLibrary request: {e}")
        return None


def search_lobid_gnd_work(query_string, acceptable_authors=None):
    if not query_string:
        logger.info("No title provided. Skipping lobid-GND lookup.")
        return None

    logger.info("🔎 Searching with lobid GND (Work)...")

    try:
        base_url = "https://lobid.org/gnd/search"
        params = {
            "q": f'"{query_string}" AND type:Work',
            "filter": "+type:Work",
            "format": "json",
            "size": 10  # Get more results for better matching
        }

        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("member"):
            # If acceptable_authors is given, filter for them
            if acceptable_authors:
                for entry in data["member"]:
                    title = entry.get("preferredName", "")
                    # Extract Wikidata ID
                    wikidata_id = None
                    for entry_link in entry.get("sameAs", []):
                        link = entry_link.get("id", "")
                        if "wikidata.org/entity/" in link:
                            wikidata_id = link.split("/")[-1]
                            break
                    # Try to extract author from various fields
                    author = None
                    author_fields = ["firstAuthor", "author", "creator"]
                    for field in author_fields:
                        if entry.get(field):
                            if isinstance(entry[field], list) and len(entry[field]) > 0:
                                author = entry[field][0].get("label")
                                break
                            elif isinstance(entry[field], dict):
                                author = entry[field].get("label")
                                break
                    # Return the first work with a matching author
                    if author and any(a in author for a in acceptable_authors):
                        return {
                            "id": entry.get("id"),
                            "title": title,
                            "author": author,
                            "gndIdentifier": entry.get("gndIdentifier"),
                            "wikidata": wikidata_id,
                            "_raw_response": json.dumps(data, ensure_ascii=False)
                        }
            # Fallback: return the first result (no author filtering)
            entry = data["member"][0]
            title = entry.get("preferredName", "")
            wikidata_id = None
            for entry_link in entry.get("sameAs", []):
                link = entry_link.get("id", "")
                if "wikidata.org/entity/" in link:
                    wikidata_id = link.split("/")[-1]
                    break
            author = None
            author_fields = ["firstAuthor", "author", "creator"]
            for field in author_fields:
                if entry.get(field):
                    if isinstance(entry[field], list) and len(entry[field]) > 0:
                        author = entry[field][0].get("label")
                        break
                    elif isinstance(entry[field], dict):
                        author = entry[field].get("label")
                        break
            return {
                "id": entry.get("id"),
                "title": title,
                "author": author,
                "gndIdentifier": entry.get("gndIdentifier"),
                "wikidata": wikidata_id,
                "_raw_response": json.dumps(data, ensure_ascii=False)
            }
        logger.info(f"⚠️ No book found for query: {query_string}")
        return None

    except Exception as e:
        logger.error(f"❌ Error in lobid-GND request: {e}")
        return None


def search_swisscovery(query_string, language="de"):
    """
    Search in swisscovery (SLSP) via SRU interface.
    See: https://slsp.ch/metadaten/
    """
    if not query_string:
        logger.info("No title provided. Skipping swisscovery lookup.")
        return None
    logger.info(f"🔎 Searching with swisscovery (SRU) for: {query_string}")
    try:
        base_url = "https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK"
        params = {
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": f'title="{query_string}"',
            "maximumRecords": "1",
            "recordSchema": "marcxml"
        }
        # Log the full request URL for debugging
        full_url = base_url + "?" + urllib.parse.urlencode(params)
        logger.info(f"SRU-Request-URL: {full_url}")
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        xml_text = response.content.decode('utf-8')
        logger.info(f"SRU-Response (first 500 chars): {xml_text[:500]}")
        if '<?xml' not in xml_text:
            xml_text = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_text
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"❌ XML Parse Error: {e}\nResponse: {xml_text[:500]}")
            return None
        ns = {
            'marc': 'http://www.loc.gov/MARC21/slim',
            'srw': 'http://www.loc.gov/zing/srw/',
            'diag': 'http://www.loc.gov/zing/srw/diagnostic/'
        }
        # Check for diagnostics (error messages from the SRU API)
        diag = root.find('.//srw:diagnostics', ns)
        if diag is not None:
            diag_msg = diag.find('.//diag:message', ns)
            diag_uri = diag.find('.//diag:uri', ns)
            logger.error(f"❌ SRU Diagnostic: {diag_msg.text if diag_msg is not None else ''} (Code: {diag_uri.text if diag_uri is not None else ''})\nResponse: {xml_text[:500]}")
            return None
        records = root.findall('.//marc:record', ns)
        if not records:
            logger.info(f"⚠️ No book found for query: {query_string}\nResponse: {xml_text[:500]}")
            return None
        record = records[0]
        def get_marc_subfield(record, tag, code):
            try:
                # Extract MARC subfield value for a given tag and code
                for field in record.findall(f".//marc:datafield[@tag='{tag}']", ns):
                    for subfield in field.findall(f"marc:subfield[@code='{code}']", ns):
                        if subfield.text and subfield.text.strip():
                            return subfield.text.strip()
            except Exception as e:
                logger.warning(f"⚠️ Error extracting MARC field {tag}${code}: {e}")
            return None
        title = get_marc_subfield(record, '245', 'a')
        author = get_marc_subfield(record, '100', 'a') or get_marc_subfield(record, '700', 'a')
        year = (get_marc_subfield(record, '264', 'c') or get_marc_subfield(record, '260', 'c'))
        isbn = get_marc_subfield(record, '020', 'a')
        if isbn:
            # Clean ISBN (remove non-numeric and non-X characters)
            isbn = re.sub(r'[^0-9X]', '', isbn)
            if len(isbn) >= 13 and isbn.startswith('97'):
                isbn = isbn[:13]
            else:
                isbn = None
        if year:
            # Extract 4-digit year
            year_match = re.search(r'\d{4}', year)
            year = year_match.group(0) if year_match else None
        result = {
            "title": title,
            "authors": author,
            "year": year,
            "isbn": isbn,
            "_raw_response": xml_text
        }
        return result
    except requests.RequestException as e:
        logger.error(f"❌ Error in swisscovery request: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Error in swisscovery processing: {e}")
        return None


def lookup_book_details(query_string, language="de", market="CH"):
    """
    Lookup book details from multiple sources and return the first successful result.
    
    Args:
        query_string (str): The query string to search for
        language (str): The language code (default: "de")
        market (str): Marktpräferenz, z.B. "CH" für Schweiz
        
    Returns:
        tuple: (source, result) where source is the name of the source that provided the result
               and result is the book details dictionary, or (None, None) if no results found
    """
    
    if not query_string:
        logger.info("No title provided. Skipping lookup.")
        return None, None

    # Für Schweizer Markt: Swisscovery zuerst
    if market == "CH":
        result = search_swisscovery(query_string, language)
        if result:
            return "Swisscovery", result

    # Dann DNB
    result = search_dnb(query_string, language)
    if result:
        return "DNB", result

    # Fallback: OpenLibrary
    logger.info("🔄 Fallback: Searching with OpenLibrary...")
    result = search_openlibrary(query_string, language)
    if result:
        return "OpenLibrary", result

    # Optional: lobid GND supplementary (authority data)
    logger.info("🔄 Additional attempt with lobid GND (authority data)...")
    result = search_lobid_gnd_work(query_string)
    if result:
        return "lobid_GND", result
    return None, None