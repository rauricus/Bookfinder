"""
Quick validation script for the AABB detection model.
Runs inference on one or more images and saves annotated results.

Usage:
    python3 detect_aabb.py                          # all example images
    python3 detect_aabb.py example-files/books/Books_00005.png
    python3 detect_aabb.py example-files/books/     # directory
    python3 detect_aabb.py --conf 0.3               # lower confidence threshold
"""

import argparse
import math
import os
import sys

import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Colors

import config

_colors = Colors()


def draw_detections(image, boxes):
    """Draw numbered, per-box-colored bounding boxes on image (in-place copy)."""
    out = image.copy()
    for i, box in enumerate(boxes):
        x1, y1, x2, y2 = (int(v) for v in box.xyxy[0].tolist())
        w, h = x2 - x1, y2 - y1
        tilt_deg = math.degrees(math.atan(w / h)) if h > w else math.degrees(math.atan(h / w))
        orientation = "upright" if h > w else "sideways"

        color = _colors(i, bgr=True)
        label = f"#{i} {orientation} {tilt_deg:.0f}deg"

        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(out, (x1, y1 - th - baseline - 4), (x1 + tw + 4, y1), color, -1)
        cv2.putText(out, label, (x1 + 2, y1 - baseline - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)
    return out

MODEL_PATH = os.path.join(config.MODEL_DIR, "aabb/YOLO11-n/detect-book-spines.train1.pt")
DEFAULT_SOURCE = os.path.join(config.HOME_DIR, "example-files/books")
OUTPUT_DIR = os.path.join(config.HOME_DIR, "output/detect_aabb")


def main():
    parser = argparse.ArgumentParser(description="Validate AABB book spine detection model.")
    parser.add_argument("source", nargs="?", default=DEFAULT_SOURCE,
                        help="Image file or directory (default: example-files/books/)")
    parser.add_argument("--conf", type=float, default=0.5,
                        help="Confidence threshold (default: 0.5)")
    parser.add_argument("--no-save", action="store_true",
                        help="Don't save annotated images, just print results")
    args = parser.parse_args()

    if not os.path.exists(MODEL_PATH):
        print(f"Model not found: {MODEL_PATH}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.source):
        print(f"Source not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    model = YOLO(MODEL_PATH)
    print(f"Model: {MODEL_PATH}")
    print(f"Source: {args.source}")
    print(f"Conf: {args.conf}")
    print()

    results = model.predict(args.source, conf=args.conf, verbose=False)

    total_detections = 0
    for result in results:
        n = len(result.boxes) if result.boxes is not None else 0
        total_detections += n

        source_name = os.path.basename(result.path)
        print(f"{source_name}: {n} book spine(s) detected")

        if n > 0 and result.boxes is not None:
            for i, box in enumerate(result.boxes):
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                w, h = x2 - x1, y2 - y1
                if h > w:
                    orientation = "upright"
                    # Estimated tilt from vertical: arctan(w/h), assuming thin spine.
                    # Lower bound — thicker books tilt less for the same ratio.
                    tilt_deg = math.degrees(math.atan(w / h))
                else:
                    orientation = "sideways"
                    tilt_deg = math.degrees(math.atan(h / w))
                print(f"  [{i}] conf={box.conf[0]:.2f}  "
                      f"w={int(w)} h={int(h)}  ratio={h/w:.2f}  "
                      f"tilt≤{tilt_deg:.1f}°  → {orientation}")

        if not args.no_save:
            annotated = draw_detections(result.orig_img, result.boxes)
            out_path = os.path.join(OUTPUT_DIR, source_name)
            cv2.imwrite(out_path, annotated)

    print()
    print(f"Total: {total_detections} detection(s) across {len(results)} image(s)")
    if not args.no_save:
        print(f"Annotated images saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
