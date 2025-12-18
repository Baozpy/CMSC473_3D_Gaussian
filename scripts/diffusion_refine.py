#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image
import torch
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel


def refine_images(
    input_dir: Path,
    output_dir: Path,
    model_id: str,
    controlnet_id: str,
    device: str,
    num_steps: int = 20,
    guidance_scale: float = 6.0,
    prompt: str = "high quality, sharp, realistic photo of a bicycle scene, same viewpoint",
):
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Input dir : {input_dir}")
    print(f"[INFO] Output dir: {output_dir}")
    print(f"[INFO] Model     : {model_id}")
    print(f"[INFO] ControlNet: {controlnet_id}")
    print(f"[INFO] Device    : {device}")

    image_paths = sorted(
        p for p in input_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )
    if not image_paths:
        raise RuntimeError(f"No images found in {input_dir}")

    # Load ControlNet + SD
    controlnet = ControlNetModel.from_pretrained(
        controlnet_id,
        torch_dtype=torch.float16,
    ).to(device)

    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        model_id,
        controlnet=controlnet,
        torch_dtype=torch.float16,
    ).to(device)

    try:
        pipe.enable_xformers_memory_efficient_attention()
    except Exception:
        print("[WARN] xFormers not available, continuing without it.")

    for img_path in image_paths:
        print(f"[INFO] Refining {img_path.name}")
        img = Image.open(img_path).convert("RGB")

        # Use the noisy render as both image & control signal (tile-style refinement)
        out = pipe(
            prompt=prompt,
            image=img,
            control_image=img,
            num_inference_steps=num_steps,
            guidance_scale=guidance_scale,
        )
        refined = out.images[0]

        out_path = output_dir / img_path.name
        refined.save(out_path)
        print(f"[OK] Saved refined: {out_path}")

    print("[DONE] Diffusion refinement complete.")


def main():
    parser = argparse.ArgumentParser(
        description="Refine SparseGS novel-view renders with diffusion (Diffix-lite)."
    )
    parser.add_argument("--input", type=Path, required=True,
                        help="Folder with noisy renders from SparseGS.")
    parser.add_argument("--output", type=Path, required=True,
                        help="Folder where refined images will be saved.")
    parser.add_argument("--model", type=str,
                        default="runwayml/stable-diffusion-v1-5",
                        help="Stable Diffusion model id.")
    parser.add_argument("--controlnet", type=str,
                        default="lllyasviel/sd-controlnet-tile",
                        help="ControlNet model id.")
    parser.add_argument("--device", type=str,
                        default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--guidance", type=float, default=6.0)
    parser.add_argument("--prompt", type=str,
                        default="high quality, sharp, realistic photo of a bicycle scene, same viewpoint")
    args = parser.parse_args()

    refine_images(
        input_dir=args.input,
        output_dir=args.output,
        model_id=args.model,
        controlnet_id=args.controlnet,
        device=args.device,
        num_steps=args.steps,
        guidance_scale=args.guidance,
        prompt=args.prompt,
    )


if __name__ == "__main__":
    main()
