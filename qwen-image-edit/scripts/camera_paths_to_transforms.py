#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert Nerfstudio ns-viewer camera-path JSON -> NeRF-style transforms_train.json
(blender_data style file_path WITHOUT extension).

Example output file_path: "images/frame_00001"  (no .png/.jpg)

Usage:
  python camerapath_to_transforms.py \
    --camera-path 2025-12-14-16-32-06.json \
    --out transforms_train.json \
    --image-dir images

If you believe camera_path[*].fov is HORIZONTAL FOV (not vertical),
add: --assume-fov-horizontal
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(obj: Dict[str, Any], p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def unflatten_4x4_row_major(a16: List[float]) -> List[List[float]]:
    if not (isinstance(a16, list) and len(a16) == 16):
        raise ValueError("camera_to_world must be a list of 16 numbers (row-major).")
    return [[float(a16[r * 4 + c]) for c in range(4)] for r in range(4)]


def deg2rad(d: float) -> float:
    return float(d) * math.pi / 180.0


def vertical_fov_to_horizontal_fov(vfov_rad: float, aspect: float) -> float:
    # hfov = 2*atan(tan(vfov/2) * aspect)
    return 2.0 * math.atan(math.tan(vfov_rad / 2.0) * float(aspect))


def build_transforms(
    camerapath: Dict[str, Any],
    out_path: Path,
    image_dir: str,
    ext: str,
    assume_fov_horizontal: bool,
    keep_existing_aspect: bool,
) -> Dict[str, Any]:
    cp = camerapath.get("camera_path")
    if not isinstance(cp, list) or len(cp) == 0:
        raise ValueError("camera-path JSON must contain a non-empty 'camera_path' list.")

    # Determine default aspect
    def_aspect = 1.0
    rw, rh = camerapath.get("render_width"), camerapath.get("render_height")
    if isinstance(rw, (int, float)) and isinstance(rh, (int, float)) and float(rh) != 0.0:
        def_aspect = float(rw) / float(rh)

    default_fov_deg = float(camerapath.get("default_fov", 75.0))

    frames: List[Dict[str, Any]] = []
    camera_angle_x_rad: Optional[float] = None

    # Normalize ext: allow "" (blender_data style). If user passes "png", treat as ".png".
    if ext and not ext.startswith("."):
        ext = "." + ext

    image_dir = image_dir.rstrip("/")

    for i, node in enumerate(cp):
        if not isinstance(node, dict) or "camera_to_world" not in node:
            raise ValueError(f"camera_path[{i}] missing 'camera_to_world'.")

        m4 = unflatten_4x4_row_major(node["camera_to_world"])

        # blender_data: file_path WITHOUT extension by default
        file_path = f"{image_dir}/r_{i}{ext}" if ext else f"{image_dir}/r_{i}"

        frames.append(
            {
                "file_path": file_path,
                "transform_matrix": m4,
            }
        )

        # Compute camera_angle_x from first frame's fov/aspect (best-effort)
        if camera_angle_x_rad is None:
            fov_deg = float(node.get("fov", default_fov_deg))
            fov_rad = deg2rad(fov_deg)

            aspect = float(node.get("aspect", def_aspect)) if keep_existing_aspect else def_aspect

            if assume_fov_horizontal:
                camera_angle_x_rad = fov_rad
            else:
                camera_angle_x_rad = vertical_fov_to_horizontal_fov(fov_rad, aspect)

    if camera_angle_x_rad is None:
        camera_angle_x_rad = deg2rad(default_fov_deg)

    out = {
        "camera_angle_x": float(camera_angle_x_rad),
        "frames": frames,
    }

    save_json(out, out_path)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera-path", required=True, type=Path, help="ns-viewer camera-path JSON")
    ap.add_argument("--out", required=True, type=Path, help="output transforms_train.json")
    ap.add_argument("--image-dir", default="images", help="file_path prefix used in frames[].file_path")
    ap.add_argument(
        "--ext",
        default="",
        help="image extension. default '' -> blender_data style (no extension). e.g. '.png' or 'png' if you want one.",
    )
    ap.add_argument(
        "--assume-fov-horizontal",
        action="store_true",
        help="treat camera_path[*].fov as horizontal FOV; otherwise assume vertical and convert to camera_angle_x",
    )
    ap.add_argument(
        "--keep-existing-aspect",
        action="store_true",
        help="use per-node aspect if present; otherwise use render_width/render_height aspect",
    )
    args = ap.parse_args()

    camerapath = load_json(args.camera_path)

    build_transforms(
        camerapath=camerapath,
        out_path=args.out,
        image_dir=args.image_dir,
        ext=args.ext,
        assume_fov_horizontal=args.assume_fov_horizontal,
        keep_existing_aspect=args.keep_existing_aspect,
    )

    print(f"[OK] Wrote blender_data-style transforms to: {args.out}")


if __name__ == "__main__":
    main()
