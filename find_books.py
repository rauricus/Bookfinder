import os
import sys
import argparse

from libs.book_finder import BookFinder


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(description="Detect and look up books in an image (or video).")
    parser.add_argument("source", type=str, nargs='?', help="Path to image, video, or directory.'")
    parser.add_argument('--debug','-d', action='count', default=0, help="Enable debug mode. (level 1: show detections)")
    args = parser.parse_args()

    book_finder = BookFinder(debug=args.debug)
    book_finder.findBooks(args.source)
