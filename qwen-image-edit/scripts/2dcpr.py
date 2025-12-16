import argparse
import csv
import json
from pathlib import Path

import numpy as np
import torch
import lpips
import matplotlib.pyplot as plt

from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity


IMG_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def list_images(folder: Path) -> dict[str, Path]:
    """Map filename -> path for images in folder (non-recursive)."""
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    out = {}
    for p in folder.iterdir():
        if p.is_file() and p.suffix.lower() in IMG_EXTS:
            out[p.name] = p
    return out


def load_image_rgb01(path: Path) -> np.ndarray:
    """Load image as float32 RGB in [0,1], shape (H,W,3)."""
    img = Image.open(path).convert("RGB")
    arr = np.asarray(img).astype(np.float32) / 255.0
    return arr


def to_lpips_tensor(img01: np.ndarray) -> torch.Tensor:
    """numpy (H,W,3) [0,1] -> torch (1,3,H,W) [-1,1]."""
    t = torch.from_numpy(img01).permute(2, 0, 1).unsqueeze(0)
    t = t * 2.0 - 1.0
    return t


def compute_pair_metrics(img_a01: np.ndarray, img_b01: np.ndarray, lpips_fn) -> tuple[float, float, float]:
    """Compute PSNR, SSIM, LPIPS for a matched pair."""
    if img_a01.shape != img_b01.shape:
        raise ValueError(f"Size mismatch: {img_a01.shape} vs {img_b01.shape}")

    psnr = peak_signal_noise_ratio(img_a01, img_b01, data_range=1.0)
    ssim = structural_similarity(img_a01, img_b01, channel_axis=-1, data_range=1.0)

    with torch.no_grad():
        a_t = to_lpips_tensor(img_a01)
        b_t = to_lpips_tensor(img_b01)
        lp = lpips_fn(a_t, b_t).item()

    return float(psnr), float(ssim), float(lp)


def summarize(values: list[float]) -> dict:
    arr = np.array(values, dtype=np.float64)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()) if arr.size else float("nan"),
        "std": float(arr.std(ddof=0)) if arr.size else float("nan"),
        "min": float(arr.min()) if arr.size else float("nan"),
        "q1": float(np.percentile(arr, 25)) if arr.size else float("nan"),
        "median": float(np.median(arr)) if arr.size else float("nan"),
        "q3": float(np.percentile(arr, 75)) if arr.size else float("nan"),
        "max": float(arr.max()) if arr.size else float("nan"),
    }


def save_hist(values, title, xlabel, out_png: Path, bins=30):
    plt.figure()
    plt.hist(values, bins=bins)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def save_boxplot(values, title, ylabel, out_png: Path):
    plt.figure()
    plt.boxplot(values, vert=True)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def save_scatter(x, y, title, xlabel, ylabel, out_png: Path):
    plt.figure()
    plt.scatter(x, y, s=10)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    plt.close()


def save_side_by_side(img_a01: np.ndarray, img_b01: np.ndarray, out_path: Path):
    """
    Create side-by-side comparison image:
    left = folder A, right = folder B
    """
    if img_a01.shape != img_b01.shape:
        raise ValueError(f"Size mismatch for qualitative: {img_a01.shape} vs {img_b01.shape}")

    h, w, _ = img_a01.shape
    canvas = np.zeros((h, w * 2, 3), dtype=np.float32)
    canvas[:, :w] = img_a01
    canvas[:, w:] = img_b01
    canvas = (canvas * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(canvas).save(out_path)


def write_markdown_report(out_dir: Path, summary: dict, topk: dict, lpips_net: str):
    md = []
    md.append("# Metrics Report\n\n")
    md.append(f"- Pairs evaluated: **{summary['psnr']['count']}**\n")
    md.append(f"- LPIPS backbone: **{lpips_net}**\n\n")

    md.append("## Overall Summary\n\n")
    md.append("| Metric | mean | std | min | q1 | median | q3 | max |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|\n")
    for k in ["psnr", "ssim", "lpips"]:
        s = summary[k]
        md.append(
            f"| {k.upper()} | {s['mean']:.4f} | {s['std']:.4f} | {s['min']:.4f} | {s['q1']:.4f} | {s['median']:.4f} | {s['q3']:.4f} | {s['max']:.4f} |\n"
        )
    md.append("\n")

    md.append("## Distributions\n\n")
    md.append("![PSNR histogram](plots/psnr_hist.png)\n\n")
    md.append("![SSIM histogram](plots/ssim_hist.png)\n\n")
    md.append(f"![LPIPS histogram](plots/lpips_hist.png)\n\n")
    md.append("![PSNR boxplot](plots/psnr_box.png)\n\n")
    md.append("![SSIM boxplot](plots/ssim_box.png)\n\n")
    md.append("![LPIPS boxplot](plots/lpips_box.png)\n\n")

    md.append("## Correlations\n\n")
    md.append("![LPIPS vs PSNR](plots/lpips_vs_psnr.png)\n\n")
    md.append("![LPIPS vs SSIM](plots/lpips_vs_ssim.png)\n\n")

    md.append("## Best / Worst Examples (Top-K)\n\n")

    def table_block(title, rows):
        md.append(f"### {title}\n\n")
        md.append("| rank | filename | value |\n")
        md.append("|---:|---|---:|\n")
        for i, r in enumerate(rows, 1):
            md.append(f"| {i} | {r['filename']} | {r['value']:.4f} |\n")
        md.append("\n")

    table_block("Best PSNR (higher is better)", topk["best_psnr"])
    table_block("Worst PSNR (lower is worse)", topk["worst_psnr"])
    table_block("Best SSIM (higher is better)", topk["best_ssim"])
    table_block("Worst SSIM (lower is worse)", topk["worst_ssim"])
    table_block("Best LPIPS (lower is better)", topk["best_lpips"])
    table_block("Worst LPIPS (higher is worse)", topk["worst_lpips"])

    md.append("## Qualitative Comparisons\n\n")
    md.append("Each image shows **Folder A (left)** and **Folder B (right)**.\n\n")
    md.append("- Examples are saved under `examples/`.\n\n")

    md.append("### Best LPIPS examples\n\n")
    for r in topk["best_lpips"][: min(5, len(topk["best_lpips"]))]:
        md.append(f"![{r['filename']}](examples/best_lpips/{r['filename']})\n\n")

    md.append("### Worst LPIPS examples\n\n")
    for r in topk["worst_lpips"][: min(5, len(topk["worst_lpips"]))]:
        md.append(f"![{r['filename']}](examples/worst_lpips/{r['filename']})\n\n")

    (out_dir / "REPORT.md").write_text("".join(md), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder_a", required=True, help="Folder A (e.g., ground truth / reference)")
    parser.add_argument("--folder_b", required=True, help="Folder B (e.g., prediction / result)")
    parser.add_argument("--out_dir", required=True, help="Output directory (will be created)")
    parser.add_argument("--lpips_net", default="alex", choices=["alex", "vgg", "squeeze"], help="LPIPS backbone")
    parser.add_argument("--strict", action="store_true", help="Require identical filename sets")
    parser.add_argument("--topk", type=int, default=10, help="Top-K best/worst examples to export")
    args = parser.parse_args()

    folder_a = Path(args.folder_a)
    folder_b = Path(args.folder_b)
    out_dir = Path(args.out_dir)
    plots_dir = out_dir / "plots"
    examples_dir = out_dir / "examples"

    out_dir.mkdir(parents=True, exist_ok=True)
    plots_dir.mkdir(parents=True, exist_ok=True)
    examples_dir.mkdir(parents=True, exist_ok=True)

    a_map = list_images(folder_a)
    b_map = list_images(folder_b)

    a_set = set(a_map.keys())
    b_set = set(b_map.keys())

    if args.strict:
        if a_set != b_set:
            only_a = sorted(a_set - b_set)
            only_b = sorted(b_set - a_set)
            msg = ["Filename sets do not match in strict mode."]
            if only_a:
                msg.append(f"Only in A ({len(only_a)}): {only_a[:10]}{' ...' if len(only_a) > 10 else ''}")
            if only_b:
                msg.append(f"Only in B ({len(only_b)}): {only_b[:10]}{' ...' if len(only_b) > 10 else ''}")
            raise ValueError("\n".join(msg))
        names = sorted(a_set)
    else:
        names = sorted(a_set & b_set)
        if not names:
            raise ValueError("No overlapping filenames found between the two folders.")

    lpips_fn = lpips.LPIPS(net=args.lpips_net)

    rows = []
    psnrs, ssims, lpipss = [], [], []

    for name in names:
        img_a = load_image_rgb01(a_map[name])
        img_b = load_image_rgb01(b_map[name])
        psnr, ssim, lpv = compute_pair_metrics(img_a, img_b, lpips_fn)

        rows.append({"filename": name, "psnr": psnr, "ssim": ssim, "lpips": lpv})
        psnrs.append(psnr)
        ssims.append(ssim)
        lpipss.append(lpv)

    # Per-image CSV
    csv_path = out_dir / "per_image_metrics.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["filename", "psnr", "ssim", "lpips"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    # Summary JSON
    summary = {
        "psnr": summarize(psnrs),
        "ssim": summarize(ssims),
        "lpips": summarize(lpipss),
        "meta": {
            "pairs": len(rows),
            "folder_a": str(folder_a),
            "folder_b": str(folder_b),
            "lpips_net": args.lpips_net,
            "strict": bool(args.strict),
        },
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # Plots: distributions
    save_hist(psnrs, "PSNR distribution", "PSNR (higher is better)", plots_dir / "psnr_hist.png")
    save_hist(ssims, "SSIM distribution", "SSIM (higher is better)", plots_dir / "ssim_hist.png")
    save_hist(lpipss, f"LPIPS({args.lpips_net}) distribution", "LPIPS (lower is better)", plots_dir / "lpips_hist.png")

    save_boxplot(psnrs, "PSNR boxplot", "PSNR", plots_dir / "psnr_box.png")
    save_boxplot(ssims, "SSIM boxplot", "SSIM", plots_dir / "ssim_box.png")
    save_boxplot(lpipss, f"LPIPS({args.lpips_net}) boxplot", "LPIPS", plots_dir / "lpips_box.png")

    # Plots: correlations
    save_scatter(psnrs, lpipss, "LPIPS vs PSNR", "PSNR (higher is better)", "LPIPS (lower is better)",
                 plots_dir / "lpips_vs_psnr.png")
    save_scatter(ssims, lpipss, "LPIPS vs SSIM", "SSIM (higher is better)", "LPIPS (lower is better)",
                 plots_dir / "lpips_vs_ssim.png")

    # Top-K lists
    topk = max(1, args.topk)
    rows_sorted_psnr = sorted(rows, key=lambda r: r["psnr"])
    rows_sorted_ssim = sorted(rows, key=lambda r: r["ssim"])
    rows_sorted_lpips = sorted(rows, key=lambda r: r["lpips"])

    top_lists = {
        "best_psnr": [{"filename": r["filename"], "value": r["psnr"]} for r in rows_sorted_psnr[-topk:][::-1]],
        "worst_psnr": [{"filename": r["filename"], "value": r["psnr"]} for r in rows_sorted_psnr[:topk]],
        "best_ssim": [{"filename": r["filename"], "value": r["ssim"]} for r in rows_sorted_ssim[-topk:][::-1]],
        "worst_ssim": [{"filename": r["filename"], "value": r["ssim"]} for r in rows_sorted_ssim[:topk]],
        "best_lpips": [{"filename": r["filename"], "value": r["lpips"]} for r in rows_sorted_lpips[:topk]],
        "worst_lpips": [{"filename": r["filename"], "value": r["lpips"]} for r in rows_sorted_lpips[-topk:][::-1]],
    }
    (out_dir / "topk.json").write_text(json.dumps(top_lists, indent=2), encoding="utf-8")

    # Qualitative side-by-side examples
    def dump_examples(tag: str, subset: list[dict]):
        d = examples_dir / tag
        d.mkdir(parents=True, exist_ok=True)
        for r in subset:
            name = r["filename"]
            img_a = load_image_rgb01(a_map[name])
            img_b = load_image_rgb01(b_map[name])
            save_side_by_side(img_a, img_b, d / name)

    dump_examples("best_psnr", top_lists["best_psnr"])
    dump_examples("worst_psnr", top_lists["worst_psnr"])
    dump_examples("best_ssim", top_lists["best_ssim"])
    dump_examples("worst_ssim", top_lists["worst_ssim"])
    dump_examples("best_lpips", top_lists["best_lpips"])
    dump_examples("worst_lpips", top_lists["worst_lpips"])

    # Markdown report
    write_markdown_report(out_dir, summary, top_lists, args.lpips_net)

    print("=== Done ===")
    print(f"Output dir: {out_dir.resolve()}")
    print(f"- per-image CSV : {csv_path.resolve()}")
    print(f"- summary JSON  : {(out_dir / 'summary.json').resolve()}")
    print(f"- topk JSON     : {(out_dir / 'topk.json').resolve()}")
    print(f"- plots         : {plots_dir.resolve()}")
    print(f"- examples      : {examples_dir.resolve()}")
    print(f"- report (md)   : {(out_dir / 'REPORT.md').resolve()}")


if __name__ == "__main__":
    main()
