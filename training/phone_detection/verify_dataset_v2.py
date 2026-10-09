"""
verify_dataset_v2.py — Direct Fast Audit for Part 1 V2 Kaggle Dataset
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import os
import sys
import glob
import json
import xml.etree.ElementTree as ET
import cv2

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_v2_dir = os.path.join(script_dir, "dataset_v2")
    output_sample_dir = os.path.join(script_dir, "dataset_verification_samples")
    os.makedirs(output_sample_dir, exist_ok=True)

    img_dir = os.path.join(dataset_v2_dir, "Mobile_image", "Mobile_image")
    xml_dir = os.path.join(dataset_v2_dir, "Annotations", "Annotations")

    if not os.path.exists(img_dir):
        img_dir = glob.glob(os.path.join(dataset_v2_dir, "**", "Mobile_image*"), recursive=True)[0]
    if not os.path.exists(xml_dir):
        xml_dir = glob.glob(os.path.join(dataset_v2_dir, "**", "Annotations*"), recursive=True)[0]

    xml_files = glob.glob(os.path.join(xml_dir, "*.xml"))
    img_files = glob.glob(os.path.join(img_dir, "*.*"))

    print(f"Dataset path: {dataset_v2_dir}")
    print(f"Found {len(img_files)} images and {len(xml_files)} XML annotations.")

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    person_phone_count = 0
    isolated_phone_count = 0
    person_no_phone_count = 0
    total_phone_boxes = 0

    samples_info = []

    for xml_p in xml_files:
        base_name = os.path.splitext(os.path.basename(xml_p))[0]
        matched_img = None
        for img_p in img_files:
            if os.path.splitext(os.path.basename(img_p))[0] == base_name:
                matched_img = img_p
                break

        if not matched_img:
            continue

        img = cv2.imread(matched_img)
        if img is None:
            continue

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30))
        has_person = len(faces) > 0

        phone_boxes = []
        try:
            tree = ET.parse(xml_p)
            root = tree.getroot()
            for obj in root.findall("object"):
                name = obj.findtext("name", "").lower()
                if "phone" in name or "mobile" in name or "cell" in name or name == "0":
                    bndbox = obj.find("bndbox")
                    if bndbox is not None:
                        xmin = int(float(bndbox.findtext("xmin")))
                        ymin = int(float(bndbox.findtext("ymin")))
                        xmax = int(float(bndbox.findtext("xmax")))
                        ymax = int(float(bndbox.findtext("ymax")))
                        phone_boxes.append([xmin, ymin, xmax, ymax])
                        total_phone_boxes += 1
        except Exception as e:
            pass

        has_phone = len(phone_boxes) > 0

        if has_person and has_phone:
            person_phone_count += 1
            cat = "PERSON_AND_PHONE"
        elif has_phone and not has_person:
            isolated_phone_count += 1
            cat = "ISOLATED_PHONE"
        elif has_person and not has_phone:
            person_no_phone_count += 1
            cat = "PERSON_NO_PHONE"
        else:
            cat = "OTHER"

        # Overlay bounding boxes on image
        vis = img.copy()
        for (fx, fy, fw, fh) in faces:
            cv2.rectangle(vis, (fx, fy), (fx+fw, fy+fh), (255, 255, 0), 2)
            cv2.putText(vis, "Person/Face", (fx, max(15, fy-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        for (xmin, ymin, xmax, ymax) in phone_boxes:
            cv2.rectangle(vis, (xmin, ymin), (xmax, ymax), (0, 0, 255), 2)
            cv2.putText(vis, "Phone BBox", (xmin, max(15, ymin-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        if len(samples_info) < 20:
            sample_save_p = os.path.join(output_sample_dir, f"{len(samples_info)+1}_{cat}_{base_name}.jpg")
            cv2.imwrite(sample_save_p, vis)
            samples_info.append({
                "image_name": os.path.basename(matched_img),
                "category": cat,
                "faces_detected": len(faces),
                "phone_boxes": len(phone_boxes),
                "sample_image_path": sample_save_p
            })

    print("\n" + "=" * 60)
    print("  FACTUAL AUDIT SUMMARY")
    print("=" * 60)
    print(f"1. Exact Kaggle Dataset URL         : https://www.kaggle.com/datasets/dataclusterlabs/mobile-phone-image-dataset")
    print(f"2. Total Number of Images           : {len(img_files)}")
    print(f"3. Person + Phone Co-occurrence     : {person_phone_count} images")
    print(f"4. Isolated Phone Images            : {isolated_phone_count} images")
    print(f"5. Person Without Visible Phone     : {person_no_phone_count} images")
    print(f"6. Total Valid Phone Bounding Boxes : {total_phone_boxes}")
    print(f"7. Visual Evidence Samples Generated: {len(samples_info)} saved in {output_sample_dir}")

    audit_res = {
        "dataset_name": "Datacluster Labs Mobile Phone Image Dataset",
        "kaggle_url": "https://www.kaggle.com/datasets/dataclusterlabs/mobile-phone-image-dataset",
        "total_images": len(img_files),
        "person_and_phone_scenes": person_phone_count,
        "isolated_phone_images": isolated_phone_count,
        "person_no_phone_images": person_no_phone_count,
        "total_phone_bounding_boxes": total_phone_boxes,
        "sample_evidence": samples_info
    }

    with open(os.path.join(script_dir, "dataset_audit_report.json"), "w") as f:
        json.dump(audit_res, f, indent=4)

if __name__ == "__main__":
    main()
