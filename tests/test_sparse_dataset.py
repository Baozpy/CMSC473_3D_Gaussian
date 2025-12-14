import importlib
import os

import pytest

'''
Unit test for sparse_dataset.py.
It tests the sparsify function for proper sampling behavior
and error handling for invalid parameters.
'''

# Helper to create dummy images
def _make_dummy_images(dir_path, names):
    dir_path.mkdir(parents=True, exist_ok=True)
    for name in names:
        (dir_path / name).write_text("dummy")

# Test cases for sparsify function
def test_sparsify_copies_expected_sample(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"

    images = ["img1.png", "img2.png", "img3.png", "img4.png"]
    _make_dummy_images(input_dir, images)

    # Pre-populate output_dir to ensure it gets removed/recreated
    output_dir.mkdir()
    (output_dir / "old.txt").write_text("stale")

    # Import the sparse_dataset module
    sparse = importlib.import_module("pipeline.datasets.sparse_dataset")

    expected_sample = ["img1.png", "img3.png"]
    
    # Mock random.sample to return our expected sample
    def fake_sample(seq, k):
        assert k == 2
        assert set(seq) == set(images)
        return expected_sample

    monkeypatch.setattr(sparse.random, "sample", fake_sample)

    sparse.sparsify(str(input_dir), str(output_dir), sample_ratio=0.5)

    # Verify output
    assert output_dir.is_dir()
    copied = set(os.listdir(output_dir))
    assert copied == set(expected_sample)
    # Ensure stale file was removed when output_dir was recreated
    assert "old.txt" not in copied

# Test cases for sparsify function
def test_sparsify_rejects_invalid_ratio(tmp_path):
    sparse = importlib.import_module("pipeline.datasets.sparse_dataset")
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    with pytest.raises(ValueError):
        sparse.sparsify(str(input_dir), str(tmp_path / "out"), sample_ratio=0)
    with pytest.raises(ValueError):
        sparse.sparsify(str(input_dir), str(tmp_path / "out"), sample_ratio=1)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
