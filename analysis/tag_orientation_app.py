import os
import json
import cv2
from PIL import Image, ImageTk
import requests
from dotenv import load_dotenv
import argparse

# ==== Configuration ====

# Roboflow API access
load_dotenv()
API_KEY = os.getenv("API_KEY")
WORKSPACE = os.getenv("WORKSPACE")
PROJECT = os.getenv("PROJECT")

# ==== Support functions ====


def remove_tag(image_id, tag, debug=False):
    
    url_del = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT}/images/{image_id}/tags"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"operation": "remove", "tags": [tag]}
    try:
        if debug:
            print(f"Debug: REMOVE text-tag: {tag}")
            print(f"Debug: URL: {url_del}")
            print(f"Debug: Headers: {headers}")
            print(f"Debug: Data: {data}")
        r = requests.post(url_del, headers=headers, json=data)
        if debug:
            print(f"Debug: REMOVE text-tag: {r.status_code} {r.text}")
        if r.status_code != 200:
            print(f"Error removing text-tag: {r.status_code} {r.text}")
        else:
            print(f"Tag '{tag}' removed successfully from image {image_id}.")
    except Exception as e:
        print(f"Error removing text-tag: {e}")


def set_tag(image_id, tag, debug=False, last_tagged=None):
    
    if last_tagged and image_id in last_tagged:
        remove_tag(image_id, last_tagged[image_id], debug)
        
    url = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT}/images/{image_id}/tags"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {"operation": "add", "tags": [tag]}
    try:
        if debug:
            print(f"Debug: URL: {url}")
            print(f"Debug: Headers: {headers}")
            print(f"Debug: Data: {data}")
        r = requests.post(url, headers=headers, json=data)
        if debug:
            print(f"Debug: Response status: {r.status_code}, Response body: {r.text}")
        # Check for errors in the response body
        if r.status_code == 200:
            response_json = r.json()
            if "error" in response_json:
                print(f"Error in response: {response_json['error']}")
                return False
        return r.status_code == 200
    except Exception as e:
        print(f"Error tagging: {e}")
        return False


def print_help():
    help_text = """
    Text Orientation Tagging App
    
    Helps to quickly tag images in a Roboflow dataset version with tags for text orientation.
    Images are fetched from the Roboflow API and displayed one by one.
    Configure the Roboflow API access in an .env file (see .env-template).

    Key commands:
      w       Mark text as upright (text-upright)
      s       Mark text as upside down (text-upside-down)
      a       Mark text as rotated left (text-rotated-left)
      d       Mark text as rotated right (text-rotated-right)
      [Space] Skip the current image
      b       Go back to the previous image (removes your last tag and lets you correct it)
      ESC     Exit the application

    Options:
      -h, --help     Show this help text
      -d, --debug    Enable debug mode (prints API requests and responses)
      -l, --limit    Max. number of images to tag (default: all available)
    """
    print(help_text)

def get_images_without_text_tag(debug=False, limit=None):
    """
    Holt alle Bilder aus dem Projekt, die KEINEN Tag mit Prefix 'text-' haben.
    """
    url = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT}/search"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    data = {
        "fields": ["id", "name", "tags"],
        # no 'tag' parameter, so we get ALL images
    }
    if limit is not None:
        data["limit"] = limit
    
    try:
        if debug:
            print(f"Debug: URL: {url}")
            print(f"Debug: Headers: {headers}")
            print(f"Debug: Data: {data}")
        r = requests.post(url, headers=headers, json=data)
        if debug:
            print(f"Debug: Response status: {r.status_code}, Response body: {r.text}")
        if r.status_code == 200:
            response_json = r.json()
            images = response_json.get("results", [])
            # Filter: only images, which have no tag starting with "text-"
            filtered = [img for img in images if not any(t.startswith("text-") for t in img.get("tags", []))]
            if debug:
                print(f"Debug: Found {len(filtered)} images without 'text-' tag.")
            return filtered
        else:
            print(f"Error fetching images: {r.status_code} {r.text}")
            return []
    except Exception as e:
        print(f"Error fetching images: {e}")
        return []

# ==== UI ====
import tempfile
import shutil


class TagApp:
    def __init__(self, images, debug=False):
        self.images = images
        self.idx = 0
        self.total = len(images)
        self.debug = debug
        self.last_tagged = {}  # image_id -> last tag

    def download_image(self, img_info):
        image_id = img_info["id"]
        headers = {"Authorization": f"Bearer {API_KEY}"}
        
        # 1. Fetch image details (contains 'image' with 'urls' and 'original')
        details_url = f"https://api.roboflow.com/{WORKSPACE}/{PROJECT}/images/{image_id}"
        try:
            r = requests.get(details_url, headers=headers)
            if r.status_code != 200:
                print(f"Error fetching image details {image_id}: {r.status_code}")
                return None
            details = r.json()
            image_url = None
            if 'image' in details and 'urls' in details['image'] and 'original' in details['image']['urls']:
                image_url = details['image']['urls']['original']
            if not image_url:
                print(f"No image url found in details for {image_id}")
                return None
            if self.debug:
                print(f"Image download url: {image_url}")
                
            # 2. Fetch actual image
            r_img = requests.get(image_url, stream=True)
            if r_img.status_code == 200 and r_img.headers.get("Content-Type", "").startswith("image/"):
                tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
                with os.fdopen(tmp_fd, "wb") as f:
                    shutil.copyfileobj(r_img.raw, f)
                if self.debug:
                    print(f"Downloaded image to {tmp_path}")
                return tmp_path
            else:
                print(f"Error downloading image file {image_id}: {r_img.status_code} {r_img.headers.get('Content-Type')} {r_img.text[:200]}")
                return None
        except Exception as e:
            print(f"Error downloading image {image_id}: {e}")
            return None

    def show_image(self):
        img_info = self.images[self.idx]
        tmp_path = self.download_image(img_info)
        if not tmp_path or not os.path.exists(tmp_path):
            print(f"Image not found or could not be downloaded: {img_info.get('name', img_info.get('id'))}")
            return False, None
        img = cv2.imread(tmp_path)
        if img is None:
            print(f"Image could not be read: {tmp_path}")
            os.remove(tmp_path)
            return False, None
        img = cv2.resize(img, (800, 400))
        cv2.imshow("Text Orientation Tagging App", img)
        return True, tmp_path

    def set_tag(self, tag):
        img_info = self.images[self.idx]
        image_id = img_info["id"]
        ok = set_tag(image_id, tag, self.debug, self.last_tagged)
        if ok:
            self.last_tagged[image_id] = tag
        else:
            print(f"Tagging failed for image {img_info.get('name', image_id)}")
        self.idx += 1

    def run(self):
        while 0 <= self.idx < self.total:
            ok, tmp_path = self.show_image()
            if not ok:
                self.idx += 1
                continue

            key = cv2.waitKey(0) & 0xFF
            if key == ord('w'):  # Up
                self.set_tag("text-upright")
            elif key == ord('s'):  # Down
                self.set_tag("text-upside-down")
            elif key == ord('a'):  # Left
                self.set_tag("text-rotated-left")
            elif key == ord('d'):  # Right
                self.set_tag("text-rotated-right")
            elif key == ord(' '):  # Skip
                self.idx += 1
            elif key == ord('b'): # Back to previous image
                if self.idx > 0:
                    self.idx -= 1
                    print("Back to previous image.")
                else:
                    print("Already at first image.")
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                continue
            elif key == 27:  # ESC to exit
                print("Exiting application...")
                cv2.destroyAllWindows()
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
                exit(0)

            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

        print("All images tagged!")
        cv2.destroyAllWindows()

# Update the main block to handle export directory argument
if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-h", "--help", action="store_true", help="Show help text")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-l", "--limit", type=int, help="Max. number of images to tag")
    args = parser.parse_args()

    if args.help:
        print_help()
        exit(0)

    print_help()  # Show help text on start

    DEBUG_MODE = args.debug
    LIMIT = args.limit

    print("Fetching images without 'text-' tag from Roboflow...")
    images = get_images_without_text_tag(DEBUG_MODE, LIMIT)
    if not images:
        print("No images found without 'text-' tag.")
        exit(1)

    app = TagApp(images, debug=DEBUG_MODE)
    app.run()
