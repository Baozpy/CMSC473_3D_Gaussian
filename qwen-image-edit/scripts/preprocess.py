import argparse
from pathlib import Path
from PIL import Image

IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def parse_bg(bg: str):
    """
    bg formats:
      - "white" / "black"
      - "r,g,b" in [0,255]
    """
    bg = bg.strip().lower()
    if bg == "white":
        return (255, 255, 255)
    if bg == "black":
        return (0, 0, 0)

    parts = bg.split(",")
    if len(parts) != 3:
        raise ValueError('Invalid --bg. Use "white", "black", or "r,g,b" (0-255).')

    rgb = tuple(int(x) for x in parts)
    if any(x < 0 or x > 255 for x in rgb):
        raise ValueError("RGB values must be in [0,255].")
    return rgb


def composite_rgba_to_bg(img_rgba: Image.Image, bg_rgb):
    """Alpha composite RGBA onto solid bg_rgb, return RGB image."""
    bg = Image.new("RGBA", img_rgba.size, (*bg_rgb, 255))
    out = Image.alpha_composite(bg, img_rgba).convert("RGB")
    return out


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def process_one(in_path: Path, out_path: Path, bg_rgb, out_format: str, force_rgb: bool):
    img = Image.open(in_path)

    # Convert / composite
    if img.mode == "RGBA":
        img_out = composite_rgba_to_bg(img, bg_rgb)
    else:
        # Some images might be "LA", "P", etc.
        if force_rgb:
            img_out = img.convert("RGB")
        else:
            # Keep RGB if possible; otherwise convert safely
            img_out = img.convert("RGB")

    ensure_parent(out_path)

    # Save
    # For jpg, need RGB; already ensured.
    if out_format.lower() in ("jpg", "jpeg"):
        img_out.save(out_path, quality=95, subsampling=0)
    else:
        img_out.save(out_path)


def iter_images(input_dir: Path, recursive: bool):
    if recursive:
        for p in input_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in IMG_EXTS:
                yield p
    else:
        for p in input_dir.iterdir():
            if p.is_file() and p.suffix.lower() in IMG_EXTS:
                yield p


def main():
    parser = argparse.ArgumentParser(description="Composite transparent images onto a solid background.")
    parser.add_argument("--in_dir", required=True, help="Input folder")
    parser.add_argument("--out_dir", required=True, help="Output folder")
    parser.add_argument("--bg", default="white", help='Background: "white", "black", or "r,g,b" (0-255). Default: white')
    parser.add_argument("--recursive", action="store_true", help="Process subfolders recursively")
    parser.add_argument("--out_ext", default="png", choices=["png", "jpg", "jpeg"], help="Output image extension")
    parser.add_argument("--force_rgb", action="store_true", help="Force convert all images to RGB (recommended)")
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    out_dir = Path(args.out_dir)

    if not in_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {in_dir}")

    bg_rgb = parse_bg(args.bg)

    count = 0
    for in_path in iter_images(in_dir, args.recursive):
        rel = in_path.relative_to(in_dir)
        out_path = (out_dir / rel).with_suffix("." + args.out_ext)

        process_one(in_path, out_path, bg_rgb, args.out_ext, args.force_rgb)
        count += 1

    print(f"Done. Processed {count} image(s).")
    print(f"Output saved to: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
