from libs.general_utils import iso639_1_to_3
import requests
import xml.etree.ElementTree as ET

def initialize():
    # Add any necessary initialization code here
    pass

    
def search_dnb(query_string, language="de"):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup in DNB.")
        return None

    print("🔎 Suche in der DNB (SRU)...")

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
            print(f"⚠️ Kein Buch gefunden für Query: {query_string}")
            return None

        return {
            "title": title_el.text if title_el is not None else "Unbekannt",
            "authors": author_el.text if author_el is not None else "Unbekannt",
            "year": year_el.text if year_el is not None else "Unbekannt",
            "isbn": isbn_el.text if isbn_el is not None else "Unbekannt"
        }

    except Exception as e:
        print(f"❌ Fehler bei DNB-Anfrage: {e}")
        return None
    
    
def search_openlibrary(query_string, language="de"):
    """
    Sucht Buchdetails basierend auf dem Titel in der OpenLibrary-API.
    
    OpenLibrary API: https://openlibrary.org/developers/api

    Args:
        query_string (str): Die Zeichenkette mit Titel, Author, etc. des Buches, nach dem gesucht werden soll.
        language (str): Die Sprache des Buches (Standard: "de").
    
    Returns:
        dict: Ein Dictionary mit Buchdetails (Titel, Autoren, Jahr, ISBN) oder None, wenn kein Buch gefunden wurde.
    """

    if not query_string:  # Überprüfen, ob der Titel leer oder None ist
        print("Kein Titel angegeben. Überspringe Lookup in OpernLibrary.")
        return None
    
    print("🔎 Versuche Suche in der OpenLibrary...")

    base_url = "https://openlibrary.org/search.json"
    params = {
        "q": query_string,
        "lang": language,
        "limit": 1  # Nur das relevanteste Ergebnis zurückgeben
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()  # Fehler bei HTTP-Statuscodes auslösen
        data = response.json()

        if "docs" in data and len(data["docs"]) > 0:
            book = data["docs"][0]  # Das erste Ergebnis nehmen
            return {
                "title": book.get("title", "Unbekannt"),
                "authors": ", ".join(book.get("author_name", ["Unbekannt"])),
                "year": book.get("first_publish_year", "Unbekannt"),
                "isbn": book.get("isbn", ["Unbekannt"])[0] if "isbn" in book else "Unbekannt"
            }
        else:
            print(f"⚠️ Kein Buch gefunden für Query: {query_string}")
            return None

    except requests.RequestException as e:
        print(f"❌ Fehler bei OpenLibrary-Anfrage: {e}")
        return None


def search_lobid_gnd_work(query_string):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup in lobid-GND.")
        return None

    print("🔎 Suche in lobid GND (Work)...")

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
            print(f"⚠️ Kein Buch gefunden für Query: {query_string}")
            return None

    except Exception as e:
        print(f"❌ Fehler bei lobid-GND-Anfrage: {e}")
        return None


def lookup_book_details(query_string, language="de"):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup.")
        return None

    # Zuerst DNB SRU versuchen
    result = search_dnb(query_string)
    if result:
        return result

    # Fallback: OpenLibrary
    print("🔄 Fallback: Versuche Suche in OpenLibrary...")
    result = search_openlibrary(query_string, language)
    if result:
        return result

    # Optional: lobid GND ergänzend (Normdaten)
    print("🔄 Zusatzversuch mit lobid GND (Normdaten)...")
    return search_lobid_gnd_work(query_string)