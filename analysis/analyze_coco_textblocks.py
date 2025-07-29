import json
import os
import numpy as np
import argparse
from collections import defaultdict

INTEREST_CLASSES = ["author", "title", "subtitle"]

def find_coco_annotations(base_path):
    """
    Automatically finds all COCO annotation files in subdirectories.
    
    Args:
        base_path (str): Path to the base directory
    
    Returns:
        list: List of found annotation files
    """
    coco_files = []
    if not os.path.exists(base_path):
        print(f"Warning: Directory {base_path} does not exist!")
        return coco_files
    
    # Search all subdirectories
    for root, dirs, files in os.walk(base_path):
        for file in files:
            # Look for various possible annotation file names
            if file.endswith('.json') and ('annotation' in file.lower() or 'coco' in file.lower()):
                full_path = os.path.join(root, file)
                coco_files.append(full_path)
                print(f"Found: {full_path}")
    
    return sorted(coco_files)

def analyze_coco_file(coco_path):
    """
    Analyzes a COCO annotation file and collects statistics.
    
    Args:
        coco_path (str): Path to the COCO annotation file
    
    Returns:
        dict: Statistics for each class
    """
    print(f"Analyzing: {coco_path}")
    
    if not os.path.exists(coco_path):
        print(f"Warning: File {coco_path} does not exist!")
        return {cls: defaultdict(list) for cls in INTEREST_CLASSES}
    
    try:
        with open(coco_path, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading {coco_path}: {e}")
        return {cls: defaultdict(list) for cls in INTEREST_CLASSES}
    
    # Mapping category_id -> name
    cat_id_to_name = {cat["id"]: cat["name"] for cat in data["categories"]}
    # Mapping name -> category_id
    name_to_cat_id = {v: k for k, v in cat_id_to_name.items()}
    
    # Mapping image_id -> (width, height)
    img_id_to_shape = {img["id"]: (img["width"], img["height"]) for img in data["images"]}
    
    # Collect values per class
    stats = {cls: defaultdict(list) for cls in INTEREST_CLASSES}
    for ann in data["annotations"]:
        cat = cat_id_to_name.get(ann["category_id"])
        if cat not in INTEREST_CLASSES:
            continue
        img_w, img_h = img_id_to_shape[ann["image_id"]]
        x, y, w, h = ann["bbox"]
        # relative values
        rel_x = x / img_w
        rel_y = y / img_h
        rel_w = w / img_w
        rel_h = h / img_h
        rel_y_center = (y + h/2) / img_h
        stats[cat]["rel_x"].append(rel_x)
        stats[cat]["rel_y"].append(rel_y)
        stats[cat]["rel_w"].append(rel_w)
        stats[cat]["rel_h"].append(rel_h)
        stats[cat]["rel_y_center"].append(rel_y_center)
    return stats

def print_stats(stats, split_name):
    print(f"\n=== Analysis for {split_name} ===")
    for cls in INTEREST_CLASSES:
        print(f"\n--- Class: {cls} ---")
        for key in ["rel_x", "rel_y", "rel_w", "rel_h", "rel_y_center"]:
            arr = np.array(stats[cls][key])
            if len(arr) == 0:
                print(f"{key}: no data")
                continue
            print(f"{key}: Mean={arr.mean():.3f}, Median={np.median(arr):.3f}, Min={arr.min():.3f}, Max={arr.max():.3f}, Std={arr.std():.3f}, N={len(arr)}")

def merge_stats(stats_list):
    merged = {cls: defaultdict(list) for cls in INTEREST_CLASSES}
    for stats in stats_list:
        for cls in INTEREST_CLASSES:
            for key, values in stats[cls].items():
                merged[cls][key].extend(values)
    return merged

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze COCO annotations for text blocks on book spines")
    parser.add_argument(
        "dataset_path", 
        type=str, 
        help="Path to the dataset directory"
    )
    
    args = parser.parse_args()
    
    # Automatically find all COCO annotation files
    coco_files = find_coco_annotations(args.dataset_path)
    
    if not coco_files:
        print(f"No COCO annotation files found in {args.dataset_path}!")
        exit(1)
    
    print(f"\nFound files: {len(coco_files)}")
    for file in coco_files:
        print(f"  - {file}")
    
    # Analyze all found files
    all_stats = []
    for coco_path in coco_files:
        stats = analyze_coco_file(coco_path)
        all_stats.append(stats)
        
        # Show statistics for each file individually with full context
        relative_path = os.path.relpath(coco_path, args.dataset_path)
        directory_name = os.path.dirname(relative_path)
        filename = os.path.basename(coco_path)
        
        if directory_name:
            display_name = f"{directory_name}/{filename}"
        else:
            display_name = filename
            
        print_stats(stats, display_name)
    
    # Show aggregated statistics
    if len(all_stats) > 1:
        merged_stats = merge_stats(all_stats)
        print("\n" + "="*60)
        print_stats(merged_stats, "ALL FILES AGGREGATED")
