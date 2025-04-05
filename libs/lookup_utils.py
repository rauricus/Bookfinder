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
        print("Kein Titel angegeben. Überspringe Lookup.")
        return None
    
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
        print(f"❌ Fehler beim Abrufen der Buchdetails: {e}")
        return None