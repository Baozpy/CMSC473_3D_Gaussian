import json
from pathlib import Path

def merge_sampled_frames_into_transforms(
    source_transforms: str,
    target_transforms: str,
    output_transforms: str,
    step: int,
    name_prefix: str = "s_",
    file_path_prefix: str = "",   
):
    source_transforms = Path(source_transforms)
    target_transforms = Path(target_transforms)
    output_transforms = Path(output_transforms)

    with source_transforms.open("r", encoding="utf-8") as f:
        src = json.load(f)
    with target_transforms.open("r", encoding="utf-8") as f:
        tgt = json.load(f)

    src_frames = src.get("frames", [])
    tgt_frames = tgt.get("frames", [])

    if not src_frames:
        raise ValueError("source_transforms has no frames")
    if tgt_frames is None:
        raise ValueError("target_transforms frames field is missing or invalid")

    sampled = src_frames[::step]

    new_frames = []
    for i, frame in enumerate(sampled):
        nf = frame.copy()
        nf["file_path"] = f"{file_path_prefix}{name_prefix}{i}"
        new_frames.append(nf)

    out = tgt.copy()
    out["frames"] = list(tgt_frames) + new_frames

    with output_transforms.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)

    print(f"✔ Source frames: {len(src_frames)}")
    print(f"✔ Target frames: {len(tgt_frames)}")
    print(f"✔ Sampled frames appended: {len(new_frames)} (step={step})")
    print(f"✔ Output total frames: {len(out['frames'])}")
    print(f"✔ Saved to: {output_transforms}")


if __name__ == "__main__":
    SOURCE = "transforms_2.json"     
    TARGET = "transforms_train.json"          
    OUTPUT = "transforms_merged.json"   
    STEP = 25                         

    FILE_PATH_PREFIX = ""                
    NAME_PREFIX = "s_"                  

    merge_sampled_frames_into_transforms(
        source_transforms=SOURCE,
        target_transforms=TARGET,
        output_transforms=OUTPUT,
        step=STEP,
        name_prefix=NAME_PREFIX,
        file_path_prefix=FILE_PATH_PREFIX,
    )
