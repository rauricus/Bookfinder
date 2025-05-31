
import requests
import xml.etree.ElementTree as ET

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

        return {
            "title": title_el.text if title_el is not None else "Unbekannt",
            "authors": author_el.text if author_el is not None else "Unbekannt",
            "year": year_el.text if year_el is not None else "Unbekannt",
            "isbn": isbn_el.text if isbn_el is not None else "Unbekannt"
        }

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
            return {
                "title": book.get("title", "Unbekannt"),
                "authors": ", ".join(book.get("author_name", ["Unbekannt"])),
                "year": book.get("first_publish_year", "Unbekannt"),
                "isbn": book.get("isbn", ["Unbekannt"])[0] if "isbn" in book else "Unbekannt"
            }
        else:
            logger.info(f"⚠️ No book found for query: {query_string}")
            return None

    except requests.RequestException as e:
        logger.error(f"❌ Error in OpenLibrary request: {e}")
        return None


def search_lobid_gnd_work(query_string):
    
    if not query_string:
        logger.info("No title provided. Skipping lobid-GND lookup.")
        return None

    logger.info("🔎 Searching with lobid GND (Work)...")

    try:
        base_url = "https://lobid.org/gnd/search"
        params = {
            "q": query_string,
            "filter": "type:Work",
            "format": "json"
        }

        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("member"):
            entry = data["member"][0]
            wikidata_link = None
            for entry_link in entry.get("sameAs", []):
                link = entry_link.get("id", "")
                if link.startswith("http://www.wikidata.org/entity/"):
                    wikidata_link = link
                    break
            return {
                "id": entry.get("id", "Unbekannt"),
                "title": entry.get("preferredName", "Unbekannt"),
                "author": entry.get("firstAuthor", [{}])[0].get("label", "Unbekannt") if entry.get("firstAuthor") else "Unbekannt",
                "gndIdentifier": entry.get("gndIdentifier", "Unbekannt"),
                "wikidata": wikidata_link or "Unbekannt"
            }
        else:
            logger.info(f"⚠️ No book found for query: {query_string}")
            return None

    except Exception as e:
        logger.error(f"❌ Error in lobid-GND request: {e}")
        return None


def lookup_book_details(query_string, language="de"):
    
    if not query_string:
        logger.info("No title provided. Skipping lookup.")
        return None

    # Try DNB SRU first
    result = search_dnb(query_string)
    if result:
        return result

    # Fallback: OpenLibrary
    logger.info("🔄 Fallback: Searching with OpenLibrary...")
    result = search_openlibrary(query_string, language)
    if result:
        return result

    # Optional: lobid GND supplementary (authority data)
    logger.info("🔄 Additional attempt with lobid GND (authority data)...")
    return search_lobid_gnd_work(query_string)