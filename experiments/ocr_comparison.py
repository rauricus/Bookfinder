#!/usr/bin/env python3
"""
OCR Vergleichstest: EasyOCR vs Tesseract
Vergleicht verschiedene OCR-Ansätze mit und ohne Preprocessing

Verwendung:
python ocr_test.py <bild_pfad>

Beispiel:
python ocr_test.py output/predict110/book/Books_00005_rotated-180_1.jpg
"""

import sys
import os
import cv2
import numpy as np
import time
import argparse
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import OCR libraries
import pytesseract
try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

# Import our preprocessing functions
try:
    from libs.utils.image_utils import unsharp_mask
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False

def apply_current_preprocessing(img):
    """
    Wendet die aktuell verwendete Preprocessing-Pipeline an
    """
    if not LIBS_AVAILABLE:
        print("⚠️ libs.utils.image_utils nicht verfügbar - verwende einfaches Preprocessing")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
        return gray
    
    # Die aktuelle Pipeline aus dem System
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Unsharp masking für bessere Schärfe
    gray = unsharp_mask(gray)
    
    # Bilateral Filter zur Rauschreduktion
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # CLAHE für besseren Kontrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    
    return gray

def test_tesseract_ocr(img, method_name, save_debug=False):
    """
    Testet Tesseract OCR auf einem Bild
    """
    print(f"\n--- Tesseract OCR ({method_name}) ---")
    
    start_time = time.time()
    try:
        # OCR mit Deutsch und Englisch
        text = pytesseract.image_to_string(
            img, 
            lang='deu+eng', 
            config='--psm 6'
        ).strip()
        
        processing_time = time.time() - start_time
        
        print(f"✅ Verarbeitungszeit: {processing_time:.2f} Sekunden")
        print(f"📝 Textlänge: {len(text)} Zeichen")
        print(f"📖 Erkannter Text: '{text}'")
        
        if save_debug:
            debug_filename = f"debug_tesseract_{method_name.lower().replace(' ', '_')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug-Bild gespeichert: {debug_filename}")
        
        return {
            'text': text,
            'length': len(text),
            'time': processing_time,
            'method': f'Tesseract ({method_name})'
        }
        
    except Exception as e:
        print(f"❌ Tesseract OCR fehlgeschlagen: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'Tesseract ({method_name})',
            'error': str(e)
        }

def test_easyocr(img, method_name, reader=None, save_debug=False):
    """
    Testet EasyOCR auf einem Bild
    """
    if not EASYOCR_AVAILABLE:
        print(f"\n--- EasyOCR ({method_name}) ---")
        print("❌ EasyOCR nicht verfügbar - Installation erforderlich")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'EasyOCR ({method_name})',
            'error': 'EasyOCR nicht installiert'
        }
    
    print(f"\n--- EasyOCR ({method_name}) ---")
    
    # Reader erstellen falls nicht vorhanden
    if reader is None:
        print("🔄 EasyOCR Reader wird initialisiert...")
        init_start = time.time()
        reader = easyocr.Reader(['de', 'en'], gpu=False)  # GPU=False für bessere Kompatibilität
        init_time = time.time() - init_start
        print(f"✅ EasyOCR initialisiert in {init_time:.2f} Sekunden")
    
    start_time = time.time()
    try:
        # EasyOCR erkennung
        results = reader.readtext(img)
        processing_time = time.time() - start_time
        
        # Texte und Konfidenzwerte extrahieren
        texts = []
        confidences = []
        
        print(f"✅ Verarbeitungszeit: {processing_time:.2f} Sekunden")
        print(f"📊 Anzahl Erkennungen: {len(results)}")
        
        for i, (bbox, text, confidence) in enumerate(results):
            texts.append(text)
            confidences.append(confidence)
            print(f"  {i+1}. '{text}' (Konfidenz: {confidence:.3f})")
        
        # Gesamttext zusammenfügen
        full_text = ' '.join(texts)
        avg_confidence = np.mean(confidences) if confidences else 0
        
        print(f"📝 Textlänge: {len(full_text)} Zeichen")
        print(f"📈 Durchschnittliche Konfidenz: {avg_confidence:.3f}")
        print(f"📖 Gesamttext: '{full_text}'")
        
        if save_debug:
            debug_filename = f"debug_easyocr_{method_name.lower().replace(' ', '_')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug-Bild gespeichert: {debug_filename}")
        
        return {
            'text': full_text,
            'length': len(full_text),
            'time': processing_time,
            'method': f'EasyOCR ({method_name})',
            'confidence': avg_confidence,
            'detections': len(results),
            'reader': reader  # Reader für Wiederverwendung zurückgeben
        }
        
    except Exception as e:
        print(f"❌ EasyOCR fehlgeschlagen: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': f'EasyOCR ({method_name})',
            'error': str(e),
            'reader': reader
        }

def analyze_image(img_path):
    """
    Führt umfassende OCR-Analyse durch
    """
    print(f"🔍 Analysiere Bild: {img_path}")
    
    # Bild laden
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"❌ Fehler: Bild {img_path} konnte nicht geladen werden")
        return
    
    print(f"📏 Bildgröße: {img.shape}")
    
    # Graustufen-Version für Analyse
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_val = np.mean(gray)
    std_val = np.std(gray)
    print(f"📊 Bildstatistik: Mittelwert={mean_val:.1f}, Standardabweichung={std_val:.1f}")
    
    # Preprocessing anwenden
    print("\n🔄 Wende Preprocessing an...")
    preprocessed = apply_current_preprocessing(img)
    
    results = []
    easyocr_reader = None
    
    # Test 1: Tesseract ohne Preprocessing
    result = test_tesseract_ocr(gray, "ohne Preprocessing", save_debug=True)
    results.append(result)
    
    # Test 2: Tesseract mit Preprocessing
    result = test_tesseract_ocr(preprocessed, "mit Preprocessing", save_debug=True)
    results.append(result)
    
    # Test 3: EasyOCR ohne Preprocessing (auf Original RGB)
    result = test_easyocr(img, "ohne Preprocessing (RGB)", save_debug=True)
    results.append(result)
    if 'reader' in result:
        easyocr_reader = result['reader']
    
    # Test 4: EasyOCR ohne Preprocessing (auf Graustufen)
    result = test_easyocr(gray, "ohne Preprocessing (Grau)", reader=easyocr_reader, save_debug=True)
    results.append(result)
    if 'reader' in result:
        easyocr_reader = result['reader']
    
    # Test 5: EasyOCR mit Preprocessing
    result = test_easyocr(preprocessed, "mit Preprocessing", reader=easyocr_reader, save_debug=True)
    results.append(result)
    
    # Ergebnisse zusammenfassen
    print("\n" + "="*80)
    print("📊 ZUSAMMENFASSUNG DER ERGEBNISSE")
    print("="*80)
    
    # Nach Textlänge sortieren
    valid_results = [r for r in results if r['length'] > 0]
    valid_results.sort(key=lambda x: x['length'], reverse=True)
    
    print(f"{'Rang':<4} {'Methode':<30} {'Zeichen':<8} {'Zeit(s)':<8} {'Zusatz':<15}")
    print("-" * 80)
    
    for i, result in enumerate(valid_results, 1):
        zusatz = ""
        if 'confidence' in result:
            zusatz = f"Conf:{result['confidence']:.3f}"
        elif 'error' in result:
            zusatz = "FEHLER"
        
        print(f"{i:<4} {result['method']:<30} {result['length']:<8} {result['time']:<8.2f} {zusatz:<15}")
    
    # Beste Ergebnisse anzeigen
    if valid_results:
        best = valid_results[0]
        print(f"\n🏆 BESTE METHODE: {best['method']}")
        print(f"📝 Text ({best['length']} Zeichen): '{best['text'][:100]}{'...' if len(best['text']) > 100 else ''}'")
        
        if len(valid_results) > 1:
            second_best = valid_results[1]
            print(f"\n🥈 ZWEITBESTE: {second_best['method']} ({second_best['length']} Zeichen)")
    else:
        print("\n❌ Keine erfolgreichen OCR-Ergebnisse")
    
    print("\n💾 Debug-Bilder wurden gespeichert für manuelle Inspektion")

def main():
    parser = argparse.ArgumentParser(description='OCR Vergleichstest: EasyOCR vs Tesseract')
    parser.add_argument('image_path', help='Pfad zum zu analysierenden Bild')
    parser.add_argument('--no-libs', action='store_true', help='Ohne libs.utils.image_utils (für minimales Preprocessing)')
    
    args = parser.parse_args()
    
    # Pfad validieren
    img_path = Path(args.image_path)
    if not img_path.exists():
        print(f"❌ Fehler: Bild {img_path} existiert nicht")
        return 1
    
    # Verfügbarkeit prüfen
    print("🔧 Verfügbarkeit prüfen...")
    print(f"✅ Tesseract: Verfügbar")
    print(f"{'✅' if EASYOCR_AVAILABLE else '❌'} EasyOCR: {'Verfügbar' if EASYOCR_AVAILABLE else 'Nicht verfügbar'}")
    print(f"{'✅' if LIBS_AVAILABLE else '❌'} libs.utils: {'Verfügbar' if LIBS_AVAILABLE else 'Nicht verfügbar'}")
    
    if not EASYOCR_AVAILABLE:
        print("\n⚠️ EasyOCR nicht verfügbar. Installation mit:")
        print("   pip install easyocr")
        print("   Führe Test nur mit Tesseract durch...\n")
    
    # Analyse durchführen
    analyze_image(img_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
