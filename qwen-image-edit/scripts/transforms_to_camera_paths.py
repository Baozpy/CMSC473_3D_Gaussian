#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Convert NeRF-style transforms.json -> Nerfstudio ns-viewer camera-path JSON.

Typical usage:
  python transforms_to_camerapath.py \
    --transforms transforms.json \
    --template camera_path.json \
    --out out_camera_path.json

If --template is not provided, the script will create a reasonable default
camera-path JSON (1920x1080, fov=75, fps=30).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _load_json(p: Path) -> Dict[str, Any]:
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(obj: Dict[str, Any], p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _flatten_4x4(m: List[List[float]]) -> List[float]:
    if not (isinstance(m, list) and len(m) == 4 and all(isinstance(r, list) and len(r) == 4 for r in m)):
        raise ValueError("transform_matrix must be a 4x4 nested list.")
    # ns-viewer camera-path uses row-major flattening (matches your example)
    return [float(m[r][c]) for r in range(4) for c in range(4)]


def _deg(rad: float) -> float:
    return float(rad) * 180.0 / math.pi


def _pick_keyframe_indices(n: int, k: int) -> List[int]:
    """Pick k indices spread across [0, n-1]."""
    if n <= 0:
        return []
    if k <= 1:
        return [0]
    if n == 1:
        return [0] * k
    # evenly spaced including endpoints
    return [round(i * (n - 1) / (k - 1)) for i in range(k)]


def _get_aspect(render_w: float, render_h: float) -> float:
    if render_h == 0:
        return 1.0
    return float(render_w) / float(render_h)


def build_from_transforms(
    transforms: Dict[str, Any],
    template: Optional[Dict[str, Any]],
    out_path: Path,
    fps: float,
    seconds: Optional[float],
    render_size: Tuple[float, float],
    fov_deg: Optional[float],
    keyframes_k: int,
    default_transition_sec: float,
    is_cycle: bool,
    smoothness_value: float,
) -> Dict[str, Any]:
    frames = transforms.get("frames")
    if not isinstance(frames, list) or len(frames) == 0:
        raise ValueError("transforms.json must contain a non-empty 'frames' list.")

    # Extract matrices
    matrices_4x4 = []
    for i, fr in enumerate(frames):
        if not isinstance(fr, dict) or "transform_matrix" not in fr:
            raise ValueError(f"frames[{i}] missing 'transform_matrix'.")
        matrices_4x4.append(_flatten_4x4(fr["transform_matrix"]))

    # Inherit render params from template if provided
    if template is not None:
        render_w = float(template.get("render_width", render_size[0]))
        render_h = float(template.get("render_height", render_size[1]))
        fps = float(template.get("fps", fps))
        default_transition_sec = float(template.get("default_transition_sec", default_transition_sec))
        is_cycle = bool(template.get("is_cycle", is_cycle))
        smoothness_value = float(template.get("smoothness_value", smoothness_value))
        camera_type = template.get("camera_type", "perspective")
        # Prefer template default_fov if caller didn't override
        if fov_deg is None:
            fov_deg = float(template.get("default_fov", 75.0))
    else:
        render_w, render_h = render_size
        camera_type = "perspective"

    aspect = _get_aspect(render_w, render_h)

    # If still no fov, try infer from camera_angle_x (often radians)
    if fov_deg is None:
        if "camera_angle_x" in transforms:
            # Warning: many datasets store horizontal FOV here; ns-viewer fov may be interpreted differently.
            # We'll use it as-is (converted to degrees) as a best-effort default.
            try:
                fov_deg = _deg(float(transforms["camera_angle_x"]))
            except Exception:
                fov_deg = 75.0
        else:
            fov_deg = 75.0

    # Seconds default: match number of frames / fps (at least one frame)
    if seconds is None:
        seconds = max(1.0 / fps, len(matrices_4x4) / fps)

    # Build camera_path list
    camera_path_list = [
        {"camera_to_world": m, "fov": float(fov_deg), "aspect": float(aspect)}
        for m in matrices_4x4
    ]

    # Build keyframes (k poses spread across the full list)
    idxs = _pick_keyframe_indices(len(matrices_4x4), keyframes_k)
    keyframes = [
        {
            "matrix": matrices_4x4[idx],
            "fov": float(fov_deg),
            "aspect": float(aspect),
            "override_transition_enabled": False,
            "override_transition_sec": None,
        }
        for idx in idxs
    ]

    out = {
        "default_fov": float(fov_deg),
        "default_transition_sec": float(default_transition_sec),
        "keyframes": keyframes,
        "camera_type": camera_type,
        "render_height": float(render_h),
        "render_width": float(render_w),
        "fps": float(fps),
        "seconds": float(seconds),
        "is_cycle": bool(is_cycle),
        "smoothness_value": float(smoothness_value),
        "camera_path": camera_path_list,
    }

    _save_json(out, out_path)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--transforms", required=True, type=Path, help="Path to transforms.json")
    ap.add_argument("--out", required=True, type=Path, help="Output camera-path json file")
    ap.add_argument("--template", type=Path, default=None, help="Existing ns-viewer camera-path JSON to inherit settings")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--seconds", type=float, default=None)
    ap.add_argument("--render-width", type=float, default=800.0)
    ap.add_argument("--render-height", type=float, default=800.0)
    ap.add_argument("--fov", type=float, default=None, help="Override FOV in degrees (recommended if you want exact match)")
    ap.add_argument("--keyframes", type=int, default=3, help="How many keyframes to generate (default: 3)")
    ap.add_argument("--default-transition-sec", type=float, default=2.0)
    ap.add_argument("--is-cycle", action="store_true")
    ap.add_argument("--smoothness", type=float, default=0.0)
    args = ap.parse_args()

    transforms = _load_json(args.transforms)
    template = _load_json(args.template) if args.template else None

    build_from_transforms(
        transforms=transforms,
        template=template,
        out_path=args.out,
        fps=args.fps,
        seconds=args.seconds,
        render_size=(args.render_width, args.render_height),
        fov_deg=args.fov,
        keyframes_k=args.keyframes,
        default_transition_sec=args.default_transition_sec,
        is_cycle=args.is_cycle,
        smoothness_value=args.smoothness,
    )

    print(f"[OK] Wrote ns-viewer camera-path to: {args.out}")


if __name__ == "__main__":
    main()
