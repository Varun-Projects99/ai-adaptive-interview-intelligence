"""
convert_to_yolo.py — Pascal VOC XML to YOLO Normalized Annotations Converter
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
import glob
import shutil
import xml.etree.ElementTree as ET
import cv2

def convert():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_v2_dir = os.path.join(script_dir, "dataset_v2")

    print("=" * 60)
    print("  InterviewIQ Part 1 V2 — XML to YOLO Annotation Converter")
    print("=" * 60)

    # Search for xml files and image files
    xml_files = glob.glob(os.path.join(dataset_v2_dir, "**", "*.xml"), recursive=True)
    img_files = glob.glob(os.path.join(dataset_v2_dir, "**", "*.jpg"), recursive=True) + \
                glob.glob(os.path.join(dataset_v2_dir, "**", "*.jpeg"), recursive=True) + \
                glob.glob(os.path.join(dataset_v2_dir, "**", "*.png"), recursive=True)

    print(f"Found {len(xml_files)} XML annotation files and {len(img_files)} images.")

    yolo_dir = os.path.join(script_dir, "yolo_v2_dataset")
    images_dst = os.path.join(yolo_dir, "images")
    labels_dst = os.path.join(yolo_dir, "labels")

    os.makedirs(images_dst, exist_ok=True)
    os.makedirs(labels_dst, exist_ok=True)

    converted_count = 0
    box_count = 0

    for xml_path in xml_files:
        base_name = os.path.splitext(os.path.basename(xml_path))[0]

        # Match image file
        matched_img = None
        for img_p in img_files:
            if os.path.splitext(os.path.basename(img_p))[0] == base_name:
                matched_img = img_p
                break

        if not matched_img:
            continue

        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()

            size_node = root.find("size")
            if size_node is not None:
                width = int(size_node.findtext("width", "0"))
                height = int(size_node.findtext("height", "0"))
            else:
                width, height = 0, 0

            if width == 0 or height == 0:
                img = cv2.imread(matched_img)
                if img is not None:
                    height, width = img.shape[:2]

            if width == 0 or height == 0:
                continue

            yolo_lines = []
            for obj in root.findall("object"):
                name = obj.findtext("name", "").lower()
                if "phone" in name or "mobile" in name or "cell" in name or name == "0":
                    bndbox = obj.find("bndbox")
                    if bndbox is not None:
                        xmin = float(bndbox.findtext("xmin"))
                        ymin = float(bndbox.findtext("ymin"))
                        xmax = float(bndbox.findtext("xmax"))
                        ymax = float(bndbox.findtext("ymax"))

                        # Normalize
                        xc = round(((xmin + xmax) / 2.0) / width, 6)
                        yc = round(((ymin + ymax) / 2.0) / height, 6)
                        w = round((xmax - xmin) / width, 6)
                        h = round((ymax - ymin) / height, 6)

                        # Clamp [0, 1]
                        xc = max(0.0, min(1.0, xc))
                        yc = max(0.0, min(1.0, yc))
                        w = max(0.0, min(1.0, w))
                        h = max(0.0, min(1.0, h))

                        yolo_lines.append(f"0 {xc} {yc} {w} {h}")
                        box_count += 1

            if yolo_lines:
                # Copy image to yolo_v2_dataset/images
                img_ext = os.path.splitext(matched_img)[1]
                target_img_p = os.path.join(images_dst, f"{base_name}{img_ext}")
                shutil.copy(matched_img, target_img_p)

                # Write label to yolo_v2_dataset/labels
                target_lbl_p = os.path.join(labels_dst, f"{base_name}.txt")
                with open(target_lbl_p, "w") as f:
                    f.write("\n".join(yolo_lines) + "\n")

                converted_count += 1

        except Exception as e:
            print(f"Error converting {xml_path}: {e}")

    print(f"\n[SUCCESS] Converted {converted_count} images ({box_count} phone boxes) to YOLO format in: {yolo_dir}")
    return converted_count

if __name__ == "__main__":
    convert()
