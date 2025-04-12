import requests
import xml.etree.ElementTree as ET

def initialize():
    # Add any necessary initialization code here
    pass

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
            print(f"⚠️ Kein Buch gefunden für Titel: {query_string}")
            return None

    except requests.RequestException as e:
        print(f"❌ Fehler bei OpenLibrary-Anfrage: {e}")
        return None


def search_lobid_gnd_work(query_string):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup in lobid-GND.")
        return None

    print("🔎 Versuche Suche in lobid GND (Work)...")

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
            print(f"⚠️ Kein Werk gefunden für Titel: {query_string}")
            return None

    except Exception as e:
        print(f"❌ Fehler bei lobid-GND-Anfrage: {e}")
        return None


def lookup_book_details(query_string, language="de"):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup.")
        return None

    # Zuerst lobid GND Work versuchen (verwendet DNB Daten)
    result = search_lobid_gnd_work(query_string)
    if result:
        return result

    # Fallback: OpenLibrary
    print("🔄 Fallback: Versuche Suche in OpenLibrary...")
    return search_openlibrary(query_string, language)