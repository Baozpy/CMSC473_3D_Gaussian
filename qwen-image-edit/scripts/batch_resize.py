#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path
from PIL import Image

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def parse_args():
    p = argparse.ArgumentParser(
        description="Resize images to a fixed resolution ONLY if aspect ratios match exactly."
    )
    p.add_argument("--in", dest="in_dir", required=True)
    p.add_argument("--out", dest="out_dir", required=True)
    p.add_argument("--width", type=int, required=True)
    p.add_argument("--height", type=int, required=True)
    p.add_argument("--quality", type=int, default=95)
    return p.parse_args()


def main():
    args = parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target_ratio = args.width / args.height

    images = [
        p for p in sorted(in_dir.iterdir())
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTS
    ]

    if not images:
        raise RuntimeError("No supported images found")

    for p in images:
        with Image.open(p) as img:
            w, h = img.size
            if (w / h) != target_ratio:
                raise RuntimeError(
                    f"Aspect ratio mismatch, aborting!\n"
                    f"File: {p.name}\n"
                    f"Image size: {w}x{h}\n"
                    f"Target size: {args.width}x{args.height}"
                )

    for p in images:
        with Image.open(p) as img:

            if img.mode in ("RGBA", "LA"):
                white_bg = Image.new("RGB", img.size, (255, 255, 255))
                white_bg.paste(img, mask=img.split()[-1])
                img = white_bg
            else:
                img = img.convert("RGB")

            resized = img.resize(
                (args.width, args.height),
                resample=Image.Resampling.LANCZOS
            )

            out_path = out_dir / p.name
            save_kwargs = {}

            if p.suffix.lower() in {".jpg", ".jpeg", ".webp"}:
                save_kwargs["quality"] = args.quality

            resized.save(out_path, **save_kwargs)
            print(f"Saved: {out_path}")

    print("All images resized with WHITE background")


if __name__ == "__main__":
    main()
