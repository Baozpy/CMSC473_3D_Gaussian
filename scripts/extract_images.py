import json
import shutil
from pathlib import Path
import argparse
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True,
                    help="Path to NeRF dataset")
    ap.add_argument("--output", required=True,
                    help="Output folder where selected images will be copied")
    ap.add_argument("--split", default="train",
                    choices=["train", "val", "test"])
    ap.add_argument("--ext", default=".png",
                    help="Image file extension (default: .png)")
    ap.add_argument("--num_images", type=int, default=None,
                    help="Number of images to copy (default: all)")
    ap.add_argument("--sample", default="first",
                    choices=["first", "random"],
                    help="How to pick images: 'first' or 'random'")

    args = ap.parse_args()

    in_dir = Path(args.input)
    out_dir = Path(args.output)
    out_images = out_dir / "images"

    out_images.mkdir(parents=True, exist_ok=True)

    # Load the transforms JSON
    tf_path = in_dir / f"transforms_{args.split}.json"
    if not tf_path.exists():
        raise FileNotFoundError(f"Missing {tf_path}")

    meta = json.loads(tf_path.read_text())
    frames = meta["frames"]

    # Pick subset
    if args.num_images is not None:
        import random
        n = min(args.num_images, len(frames))
        if args.sample == "random":
            frames = random.sample(frames, n)
        else:
            frames = frames[:n]

    print(f"[INFO] Extracting {len(frames)} images")

    # Copy selected images
    for fr in frames:
        fp = fr["file_path"]
        src = (in_dir / fp)

        # handle images without extension in JSON
        if not src.with_suffix(args.ext).exists():
            if src.exists():
                src_img = src
            else:
                raise FileNotFoundError(f"Cannot find image for frame: {fp}")
        else:
            src_img = src.with_suffix(args.ext)

        dst = out_images / src_img.name
        shutil.copy(src_img, dst)

    print(f"[OK] Copied {len(frames)} images to {out_images}")


if __name__ == "__main__":
    main()
