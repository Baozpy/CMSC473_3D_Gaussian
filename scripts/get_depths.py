import argparse
from pathlib import Path
import numpy as np
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForDepthEstimation


def get_depths(image_dir: Path, output_dir: Path, model_id: str, device: str):
    image_dir = image_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading images from: {image_dir}")

    images = sorted([p for p in image_dir.iterdir()
                     if p.suffix.lower() in {".png", ".jpg", ".jpeg"}])

    if len(images) == 0:
        raise RuntimeError(f"No images found in {image_dir}")

    print(f"[INFO] Found {len(images)} images")
    print(f"[INFO] Loading model: {model_id}")

    processor = AutoImageProcessor.from_pretrained(model_id)
    model = AutoModelForDepthEstimation.from_pretrained(model_id)
    model = model.to(device).eval()

    raw_depths = []

    # --------------------------
    # First pass: compute depths
    # --------------------------
    for img_path in images:
        img = Image.open(img_path).convert("RGB")
        inputs = processor(images=img, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            depth = model(**inputs).predicted_depth.squeeze().float().cpu().numpy()

        raw_depths.append((img_path, depth))

    # -------------------------------------------------
    # Second pass: global scene-level min/max normalize
    # -------------------------------------------------
    all_vals = np.concatenate([d.flatten() for _, d in raw_depths])
    glob_min, glob_max = float(all_vals.min()), float(all_vals.max())

    print(f"[INFO] Global depth range: [{glob_min:.4f}, {glob_max:.4f}]")

    for img_path, depth in raw_depths:
        norm_depth = (depth - glob_min) / (glob_max - glob_min + 1e-6)
        out_path = output_dir / f"{img_path.stem}.npy"
        np.save(out_path, norm_depth)
        print(f"[OK] Saved normalized depth: {out_path.name}")

    print("[DONE] All depths written.")


def main():
    parser = argparse.ArgumentParser(description="Depth estimation for SparseGS")
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", type=str,
                        default="depth-anything/Depth-Anything-V2-Base-hf")
    parser.add_argument("--device", type=str,
                        default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    get_depths(args.images, args.output, args.model, args.device)


if __name__ == "__main__":
    main()
