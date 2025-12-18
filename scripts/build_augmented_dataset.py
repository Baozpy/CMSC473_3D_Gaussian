#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil
from PIL import Image
import numpy as np


def compute_diff(original_path, refined_path):
    """Return mean squared pixel error between original and refined."""
    o = np.asarray(Image.open(original_path).convert("RGB"), dtype=np.float32) / 255.0
    r = np.asarray(Image.open(refined_path).convert("RGB"), dtype=np.float32) / 255.0
    diff = np.mean((o - r) ** 2)
    return diff


def select_refined_images(original_dir, refined_dir, threshold=0.12):
    """
    Returns list of filenames to keep.
    low diff → stable → keep.
    high diff → hallucinated → reject.
    """
    original_dir = Path(original_dir)
    refined_dir = Path(refined_dir)

    keep = []
    skip = []

    refined_paths = sorted(refined_dir.glob("*.png"))
    for refined_path in refined_paths:
        orig_path = original_dir / refined_path.name
        if not orig_path.exists():
            print(f"[WARN] Original image {orig_path} missing, skipping.")
            continue

        score = compute_diff(orig_path, refined_path)

        if score < threshold:
            print(f"[KEEP] {refined_path.name}  (diff={score:.4f})")
            keep.append(refined_path.name)
        else:
            print(f"[SKIP] {refined_path.name}  (diff={score:.4f})")
            skip.append(refined_path.name)

    print(f"\nKept {len(keep)} / {len(refined_paths)} refined images.")
    return keep

def copy_dataset(orig_dataset, out_dataset):
    orig_dataset = Path(orig_dataset)
    out_dataset = Path(out_dataset)

    if out_dataset.exists():
        print(f"[INFO] Output dataset {out_dataset} already exists, reusing.")
    else:
        print(f"[INFO] Copying dataset: {orig_dataset} -> {out_dataset}")
        shutil.copytree(orig_dataset, out_dataset)

    print("[OK] Dataset prepared.\n")


def add_filtered_images(out_dataset, refined_dir, keep_list, prefix="aug_"):
    img_dir = Path(out_dataset) / "images"
    img_dir.mkdir(exist_ok=True)

    name_pairs = []

    for filename in keep_list:
        src = Path(refined_dir) / filename
        dst_name = prefix + filename
        dst = img_dir / dst_name

        shutil.copy2(src, dst)
        print(f"[ADD] {filename} -> {dst_name}")

        name_pairs.append((filename, dst_name))

    print(f"[OK] Added {len(name_pairs)} filtered refined images.\n")
    return name_pairs

def update_images_txt(out_dataset, name_pairs, sparse_subdir="sparse/0"):
    sparse_dir = Path(out_dataset) / sparse_subdir
    images_txt = sparse_dir / "images.txt"

    print(f"[INFO] Updating {images_txt}")

    with images_txt.open("r") as f:
        lines = f.readlines()

    # Find max existing ID
    max_id = -1
    for line in lines:
        parts = line.strip().split()
        if len(parts) > 0:
            try:
                curr_id = int(parts[0])
                max_id = max(max_id, curr_id)
            except ValueError:
                pass

    next_id = max_id + 1
    print(f"[INFO] Starting augmented IDs from {next_id}\n")

    new_lines = lines[:]
    appended_blocks = []

    for orig_name, new_name in name_pairs:
        print(f"[PROCESS] Adding {new_name} (from {orig_name})")

        found = False

        for i, line in enumerate(lines):
            if orig_name in line:
                found = True

                header = line.rstrip("\n")
                matches = lines[i + 1]

                parts = header.split()

                # Replace ID and filename
                parts[0] = str(next_id)
                parts[-1] = new_name

                new_header = " ".join(parts) + "\n"

                appended_blocks.append(new_header)
                appended_blocks.append(matches)

                next_id += 1
                break

        if not found:
            print(f"[WARN] Could not find pose for {orig_name} in images.txt")

    new_lines.extend(appended_blocks)

    with images_txt.open("w") as f:
        f.writelines(new_lines)

    print(f"[DONE] Added {len(appended_blocks)//2} augmented pose entries.\n")

def main():
    parser = argparse.ArgumentParser(description="Build augmented dataset with filtered diffusion-refined views.")
    parser.add_argument("--orig_dataset", type=Path, required=True)
    parser.add_argument("--refined_renders", type=Path, required=True)
    parser.add_argument("--original_renders", type=Path, required=True,
                        help="Original SparseGS novel renders to compare against.")
    parser.add_argument("--out_dataset", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.12,
                        help="Filtering threshold for refined images.")
    parser.add_argument("--prefix", type=str, default="aug_")
    args = parser.parse_args()

    copy_dataset(args.orig_dataset, args.out_dataset)

    print("=== Selecting refined images ===")
    keep_list = select_refined_images(
        original_dir=args.original_renders,
        refined_dir=args.refined_renders,
        threshold=args.threshold
    )

    print("\n=== Adding filtered refined images ===")
    name_pairs = add_filtered_images(
        out_dataset=args.out_dataset,
        refined_dir=args.refined_renders,
        keep_list=keep_list,
        prefix=args.prefix
    )

    print("\n=== Updating COLMAP images.txt ===")
    update_images_txt(
        out_dataset=args.out_dataset,
        name_pairs=name_pairs
    )

    print("\n[ALL DONE] Augmented dataset created.")


if __name__ == "__main__":
    main()
