import importlib
import os
import re

import pytest
from PIL import Image

'''
Unit test for resize_input.py.
It tests the resize_input function for proper
directory checks and image resizing/renaming behavior.
'''
# Helper to create a simple image
def _make_image(path, size, color=(50, 50, 50)):
    Image.new("RGB", size, color=color).save(path)

# Test cases for resize_input function
def test_resize_input_validates_directory(tmp_path):
    api = importlib.import_module("pipeline.resize_input")
    with pytest.raises(ValueError):
        api.resize_input(str(tmp_path / "missing"))

# Test cases for resize_input function
def test_resize_input_resizes_all_images(tmp_path):
    input_dir = tmp_path / "images"
    input_dir.mkdir()

    # Reference image sets target size (width -> ~1248)
    _make_image(input_dir / "ref.png", (2496, 1664))  # factor=2 -> new size (1248, 832)
    _make_image(input_dir / "other1.png", (3000, 2000))
    _make_image(input_dir / "other2.png", (1248, 1248))

    api = importlib.import_module("pipeline.resize_input")
    api.resize_input(str(input_dir))

    # Verify all images resized and renamed correctly
    files = list(input_dir.iterdir())
    assert len(files) == 3
    names = {p.name for p in files}
    assert all(re.match(r"image\d+\.png", name) for name in names)

    # Verify all images have expected size
    expected_size = (1248, 832)
    for path in files:
        assert Image.open(path).size == expected_size


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
