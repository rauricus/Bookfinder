import requests

def lookup_book_details(query_string, language="de"):
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


def search_dnb(query_string):

    if not query_string:  # Überprüfen, ob der Titel leer oder None ist
        print("Kein Titel angegeben. Überspringe Lookup in DNB.")
        return None

    print("🔎 Versuche Suche in der DNB...")
    
    try:
        dnb_url = "https://services.dnb.de/sru/dnb"
        dnb_params = {
            "version": "1.1",
            "operation": "searchRetrieve",
            "query": f'ti="{query_string}"',
            "recordSchema": "dc",
            "maximumRecords": 1
        }
        dnb_response = requests.get(dnb_url, params=dnb_params, timeout=10)
        dnb_response.raise_for_status()
        root = ET.fromstring(dnb_response.content)
        ns = {'dc': 'http://purl.org/dc/elements/1.1/'}

        title_el = root.find('.//dc:title', ns)
        author_el = root.find('.//dc:creator', ns)
        year_el = root.find('.//dc:date', ns)

        if title_el is not None:
            return {
                "title": title_el.text or "Unbekannt",
                "authors": author_el.text if author_el is not None else "Unbekannt",
                "year": year_el.text if year_el is not None else "Unbekannt",
                "isbn": "Unbekannt"
            }
        else:
            return None

    except Exception as e:
        print(f"❌ Fehler bei DNB-Anfrage: {e}")
        return None


def lookup_book_details(query_string, language="de"):
    if not query_string:
        print("Kein Titel angegeben. Überspringe Lookup.")
        return None

    # Zuerst DNB versuchen
    result = search_dnb(query_string)
    if result:
        return result

    # Fallback: OpenLibrary
    print("🔄 Fallback: Versuche Suche in OpenLibrary...")
    return search_openlibrary(query_string, language)