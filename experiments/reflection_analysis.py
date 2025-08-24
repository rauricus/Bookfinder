#!/usr/bin/env python3
"""
Reflexionslinien-Analyse für Buchcover OCR
Testet verschiedene Methoden zur Behandlung von weißen Reflexionslinien

Verwendung:
python reflection_test.py <bild_pfad>
"""

import sys
import os
import cv2
import numpy as np
import time
import argparse
from pathlib import Path
import matplotlib.pyplot as plt

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

def detect_horizontal_reflections(img):
    """
    Detektiert horizontale weiße Reflexionslinien
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Finde sehr helle horizontale Strukturen
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (img.shape[1]//3, 1))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, horizontal_kernel)
    
    # Schwellenwert für Reflexionen
    _, reflection_mask = cv2.threshold(tophat, 20, 255, cv2.THRESH_BINARY)
    
    # Statistiken über Reflexionslinien
    reflection_pixels = np.sum(reflection_mask == 255)
    total_pixels = reflection_mask.shape[0] * reflection_mask.shape[1]
    reflection_percentage = (reflection_pixels / total_pixels) * 100
    
    return reflection_mask, reflection_percentage

def remove_reflections_method1(img):
    """
    Methode 1: Inpainting - Reflexionslinien durch Interpolation ersetzen
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Reflexionslinien detektieren
    reflection_mask, _ = detect_horizontal_reflections(img)
    
    # Maske etwas erweitern für besseres Inpainting
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    reflection_mask = cv2.morphologyEx(reflection_mask, cv2.MORPH_DILATE, kernel)
    
    # Inpainting anwenden
    result = cv2.inpaint(gray, reflection_mask, 3, cv2.INPAINT_TELEA)
    
    return result

def remove_reflections_method2(img):
    """
    Methode 2: Morphologische Opening - Entfernt dünne helle Linien
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Morphologische Opening um dünne helle Linien zu entfernen
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 3))
    opened = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    
    return opened

def remove_reflections_method3(img):
    """
    Methode 3: Adaptive Schwellenwert-Dämpfung
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    # Finde lokale Maxima (potentielle Reflexionen)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Bereiche, die viel heller sind als ihre Umgebung, dämpfen
    diff = gray.astype(np.float32) - blurred.astype(np.float32)
    
    # Nur sehr helle Bereiche dämpfen
    mask = diff > 30
    result = gray.copy().astype(np.float32)
    result[mask] = result[mask] * 0.7  # Reflexionen um 30% abdunkeln
    
    return result.astype(np.uint8)

def apply_current_preprocessing(img):
    """
    Aktuelle Preprocessing-Pipeline (reduziert)
    """
    if not LIBS_AVAILABLE:
        return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img.copy()
    return unsharp_mask(gray)

def test_ocr_method(img, method_name, save_debug=False):
    """
    Testet OCR auf einem verarbeiteten Bild
    """
    print(f"\n--- {method_name} ---")
    
    start_time = time.time()
    try:
        text = pytesseract.image_to_string(
            img, 
            lang='deu+eng', 
            config='--psm 6'
        ).strip()
        
        processing_time = time.time() - start_time
        
        print(f"✅ Verarbeitungszeit: {processing_time:.2f} Sekunden")
        print(f"📝 Textlänge: {len(text)} Zeichen")
        print(f"📖 Erkannter Text: '{text}'")
        
        # Suche nach bekannten Wörtern
        known_words = ['ORHAN', 'PAMUK', 'DIE', 'ROTHAARIGE', 'ROTH']
        found_words = []
        text_upper = text.upper()
        for word in known_words:
            if word in text_upper:
                found_words.append(word)
        
        if found_words:
            print(f"🎯 Erkannte Schlüsselwörter: {', '.join(found_words)}")
        
        if save_debug:
            debug_filename = f"debug_reflection_{method_name.lower().replace(' ', '_').replace('(', '').replace(')', '')}.jpg"
            cv2.imwrite(debug_filename, img)
            print(f"💾 Debug-Bild gespeichert: {debug_filename}")
        
        return {
            'text': text,
            'length': len(text),
            'time': processing_time,
            'method': method_name,
            'keywords': found_words
        }
        
    except Exception as e:
        print(f"❌ OCR fehlgeschlagen: {e}")
        return {
            'text': '',
            'length': 0,
            'time': 0,
            'method': method_name,
            'error': str(e),
            'keywords': []
        }

def analyze_reflections(img_path):
    """
    Führt umfassende Reflexionslinien-Analyse durch
    """
    print(f"🔍 Analysiere Reflexionslinien in: {img_path}")
    
    # Bild laden
    img = cv2.imread(str(img_path))
    if img is None:
        print(f"❌ Fehler: Bild {img_path} konnte nicht geladen werden")
        return
    
    print(f"📏 Bildgröße: {img.shape}")
    
    # Reflexionsanalyse
    print("\n🔬 Reflexionslinien-Analyse...")
    reflection_mask, reflection_percentage = detect_horizontal_reflections(img)
    print(f"📊 Reflexionsanteil: {reflection_percentage:.2f}% der Bildfläche")
    
    # Reflexionsmaske speichern
    cv2.imwrite("debug_reflection_mask.jpg", reflection_mask)
    print("💾 Reflexionsmaske gespeichert: debug_reflection_mask.jpg")
    
    # Graustufen-Original
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    results = []
    
    # Test 1: Original ohne Preprocessing
    result = test_ocr_method(gray, "Original (ohne Preprocessing)", save_debug=True)
    results.append(result)
    
    # Test 2: Aktuelles Preprocessing (nur Unsharp Mask)
    current_processed = apply_current_preprocessing(img)
    result = test_ocr_method(current_processed, "Aktuell (Unsharp Mask)", save_debug=True)
    results.append(result)
    
    # Test 3: Reflexionsentfernung Methode 1 (Inpainting)
    method1 = remove_reflections_method1(img)
    method1_sharpened = unsharp_mask(method1) if LIBS_AVAILABLE else method1
    result = test_ocr_method(method1_sharpened, "Inpainting + Unsharp", save_debug=True)
    results.append(result)
    
    # Test 4: Reflexionsentfernung Methode 2 (Morphologisch)
    method2 = remove_reflections_method2(img)
    method2_sharpened = unsharp_mask(method2) if LIBS_AVAILABLE else method2
    result = test_ocr_method(method2_sharpened, "Morphological + Unsharp", save_debug=True)
    results.append(result)
    
    # Test 5: Reflexionsentfernung Methode 3 (Adaptive Dämpfung)
    method3 = remove_reflections_method3(img)
    method3_sharpened = unsharp_mask(method3) if LIBS_AVAILABLE else method3
    result = test_ocr_method(method3_sharpened, "Adaptive Dämpfung + Unsharp", save_debug=True)
    results.append(result)
    
    # Ergebnisse zusammenfassen
    print("\n" + "="*80)
    print("📊 REFLEXIONSLINIEN-TEST ERGEBNISSE")
    print("="*80)
    
    # Nach Anzahl erkannter Schlüsselwörter sortieren
    results.sort(key=lambda x: len(x.get('keywords', [])), reverse=True)
    
    print(f"{'Rang':<4} {'Methode':<35} {'Zeichen':<8} {'Zeit(s)':<8} {'Schlüsselwörter':<20}")
    print("-" * 80)
    
    for i, result in enumerate(results, 1):
        keywords = ', '.join(result.get('keywords', []))
        if not keywords:
            keywords = "keine"
        
        print(f"{i:<4} {result['method']:<35} {result['length']:<8} {result['time']:<8.2f} {keywords:<20}")
    
    # Beste Methode für Schlüsselwort-Erkennung
    best_for_keywords = results[0]
    print(f"\n🏆 BESTE METHODE FÜR SCHLÜSSELWÖRTER: {best_for_keywords['method']}")
    if best_for_keywords.get('keywords'):
        print(f"🎯 Erkannte Schlüsselwörter: {', '.join(best_for_keywords['keywords'])}")
    print(f"📝 Volltext: '{best_for_keywords['text']}'")
    
    # Visualisierung erstellen
    create_visualization(img, reflection_mask, method1, method2, method3)

def create_visualization(original, reflection_mask, method1, method2, method3):
    """
    Erstellt eine Visualisierung der verschiedenen Methoden
    """
    try:
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # Original
        axes[0,0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
        axes[0,0].set_title("Original")
        axes[0,0].axis('off')
        
        # Reflexionsmaske
        axes[0,1].imshow(reflection_mask, cmap='gray')
        axes[0,1].set_title("Erkannte Reflexionslinien")
        axes[0,1].axis('off')
        
        # Graustufen Original
        gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
        axes[0,2].imshow(gray, cmap='gray')
        axes[0,2].set_title("Original Graustufen")
        axes[0,2].axis('off')
        
        # Methode 1: Inpainting
        axes[1,0].imshow(method1, cmap='gray')
        axes[1,0].set_title("Inpainting")
        axes[1,0].axis('off')
        
        # Methode 2: Morphologisch
        axes[1,1].imshow(method2, cmap='gray')
        axes[1,1].set_title("Morphological Opening")
        axes[1,1].axis('off')
        
        # Methode 3: Adaptive Dämpfung
        axes[1,2].imshow(method3, cmap='gray')
        axes[1,2].set_title("Adaptive Dämpfung")
        axes[1,2].axis('off')
        
        plt.tight_layout()
        plt.savefig("reflection_analysis_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print("\n📊 Visualisierung gespeichert: reflection_analysis_comparison.png")
        
    except Exception as e:
        print(f"⚠️ Visualisierung fehlgeschlagen: {e}")

def main():
    parser = argparse.ArgumentParser(description='Reflexionslinien-Analyse für Buchcover OCR')
    parser.add_argument('image_path', help='Pfad zum zu analysierenden Bild')
    
    args = parser.parse_args()
    
    # Pfad validieren
    img_path = Path(args.image_path)
    if not img_path.exists():
        print(f"❌ Fehler: Bild {img_path} existiert nicht")
        return 1
    
    # Verfügbarkeit prüfen
    print("🔧 Verfügbarkeit prüfen...")
    print(f"✅ Tesseract: Verfügbar")
    print(f"{'✅' if LIBS_AVAILABLE else '❌'} libs.utils: {'Verfügbar' if LIBS_AVAILABLE else 'Nicht verfügbar'}")
    
    # Analyse durchführen
    analyze_reflections(img_path)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
