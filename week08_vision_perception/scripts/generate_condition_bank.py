import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cv2
from perception.dataset import samples


def main():
    target = Path(__file__).resolve().parents[1]/"runtime/condition_bank"
    target.mkdir(parents=True, exist_ok=True)
    rows = []
    for item in samples():
        name = item["image_id"]+".png"
        cv2.imwrite(str(target/name), item["image"])
        rows.append({"image_id": item["image_id"], "condition": item["condition"], "expected": item["expected"], "image": name,"reference_box":item["reference_box"]})
    with (target/"ground_truth.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    print(target)


if __name__ == "__main__": main()
