#!/usr/bin/env python3
import argparse
from pathlib import Path
import shutil

def subsample(input_dir, output_dir, step):
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect render files (sorted ensures consistent sampling)
    files = sorted([p for p in input_dir.iterdir() if p.suffix.lower() in [".png", ".jpg", ".jpeg"]])

    if len(files) == 0:
        raise RuntimeError(f"No image files found in {input_dir}")

    print(f"[INFO] Found {len(files)} images.")
    print(f"[INFO] Keeping every {step}-th image.")

    keep_count = 0
    for i, f in enumerate(files):
        if i % step == 0:
            dst = output_dir / f.name
            shutil.copy2(f, dst)
            print(f"[KEEP] {f.name}")
            keep_count += 1
        else:
            print(f"[SKIP] {f.name}")

    print(f"\n[DONE] Kept {keep_count} / {len(files)} images.")
    print(f"Saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Subsample rendered images (keep every Nth).")
    parser.add_argument("--input", type=str, required=True,
                        help="Input folder containing full renders.")
    parser.add_argument("--output", type=str, required=True,
                        help="Output folder for subsampled renders.")
    parser.add_argument("--step", type=int, default=5,
                        help="Keep every N-th image. Default = 5.")
    args = parser.parse_args()

    subsample(args.input, args.output, args.step)


if __name__ == "__main__":
    main()
