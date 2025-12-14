import os
import re
import importlib

import pytest
from PIL import Image

'''
Unit test for resize_images.py.
It tests the concatenate_images function for proper
directory checks and image resizing/renaming behavior.
'''

# Test cases for concatenate_images function
def test_concatenate_images_directory_checks(tmp_path):
    reference_dir = tmp_path / "ref"
    target_dir = tmp_path / "tgt"

    # Only create one directory to trigger checks
    reference_dir.mkdir()

    api = importlib.import_module("pipeline.resize_images")

    with pytest.raises(ValueError):
        api.concatenate_images(str(reference_dir), str(tmp_path / "missing"))

    with pytest.raises(ValueError):
        api.concatenate_images(str(tmp_path / "missing"), str(target_dir))

# Helper to create a simple image
def _make_image(path, size, color=(100, 100, 100)):
    img = Image.new("RGB", size, color=color)
    img.save(path)

# Test cases for concatenate_images function
def test_concatenate_images_resizing_and_sizes(tmp_path):
    # Prepare reference dir with images named so last_id can be parsed
    reference_dir = tmp_path / "ref"
    reference_dir.mkdir()
    # Create multiple images with numeric ids
    _make_image(reference_dir / "image1.png", (64, 48))
    _make_image(reference_dir / "image2.png", (64, 48))
    _make_image(reference_dir / "image10.png", (64, 48))

    # Prepare target dir with subfolders each containing a *_cleaned.png
    target_dir = tmp_path / "tgt"
    target_dir.mkdir()
    for name, size in [("frameA", (120, 90)), ("frameB", (256, 128)), ("frameC", (32, 32))]:
        sub = target_dir / name
        sub.mkdir()
        _make_image(sub / f"{name}_cleaned.png", size)

    api = importlib.import_module("pipeline.resize_images")
    api.concatenate_images(str(reference_dir), str(target_dir))

    # After run, new images should be appended starting from last_id+1
    # last_id detected from ref images: max(1,2,10) = 10
    expected_names = {"image11.png", "image12.png", "image13.png"}
    produced = {p.name for p in reference_dir.iterdir() if re.match(r"image\d+\.png", p.name)}
    assert expected_names.issubset(produced)

    # Verify all new images match the reference size (from first reference image)
    reference_size = Image.open(reference_dir / "image1.png").size
    for name in expected_names:
        size = Image.open(reference_dir / name).size
        assert size == reference_size


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
