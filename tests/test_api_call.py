import importlib
import sys
import types
from pathlib import Path

import pytest
from PIL import Image

'''
Unit test for api_call.py. 
It uses fake client and model classes to simulate the behavior
of the API for testing purposes. 
'''

# Fake classes to simulate API responses
class FakeInlineData:
    def __init__(self, image: Image.Image):
        self._image = image

    def as_image(self) -> Image.Image:
        return self._image

# Fake classes to simulate API responses
class FakePart:
    def __init__(self, text=None, inline_data=None):
        self.text = text
        self.inline_data = inline_data

# Fake classes to simulate API responses
class FakeResponse:
    def __init__(self, parts, status_code=200):
        self.parts = parts
        self.status_code = status_code

# Fake classes to simulate API responses
class FakeModels:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def generate_content(self, model, contents):
        self.calls.append({"model": model, "contents": contents})
        if not self._responses:
            raise RuntimeError("No fake responses left for generate_content")
        response = self._responses.pop(0)
        if response.status_code != 200:
            raise RuntimeError(f"generate_content failed with status code {response.status_code}")
        return response

# Fake classes to simulate API responses
class FakeClient:
    def __init__(self, api_key, responses):
        self.api_key = api_key
        self.models = FakeModels(responses)

# Helper function to load api_call with fake client
def load_api_call_with_fakes(monkeypatch, responses):
    created_clients = []

    def fake_client_ctor(api_key):
        client = FakeClient(api_key, responses)
        created_clients.append(client)
        return client

    stub_genai = types.SimpleNamespace(Client=fake_client_ctor)
    monkeypatch.setitem(sys.modules, "google.genai", stub_genai)
    monkeypatch.setitem(sys.modules, "google", types.SimpleNamespace(genai=stub_genai))
    monkeypatch.setitem(sys.modules, "google.genai.types", types.SimpleNamespace())

    sys.modules.pop("pipeline.api_call", None)
    api_call = importlib.import_module("pipeline.api_call")
    return api_call, created_clients


# Test cases for clean_frames function
def test_clean_frames_saves_outputs(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    results_dir = tmp_path / "results"
    input_dir.mkdir()
    results_dir.mkdir()

    frame_path = input_dir / "frame1.png"
    Image.new("RGB", (20, 20), color=(1, 2, 3)).save(frame_path)

    depth_image = Image.new("RGB", (10, 10), color=(10, 10, 10))
    cleaned_image = Image.new("RGB", (10, 10), color=(20, 20, 20))

    responses = [
        FakeResponse([FakePart(inline_data=FakeInlineData(depth_image))]),
        FakeResponse([FakePart(inline_data=FakeInlineData(cleaned_image))]),
    ]

    api_call, clients = load_api_call_with_fakes(monkeypatch, responses)

    api_call.clean_frames("fake-key", str(input_dir), str(results_dir))

    expected = [
        results_dir / "frame1" / "frame1.png",
        results_dir / "frame1" / "frame1_low_res.png",
        results_dir / "frame1" / "frame1_depth_map.png",
        results_dir / "frame1" / "frame1_cleaned.png",
    ]
    for path in expected:
        assert path.exists()

    produced_names = {p.name for p in (results_dir / "frame1").iterdir()}
    assert produced_names == {
        "frame1.png",
        "frame1_low_res.png",
        "frame1_depth_map.png",
        "frame1_cleaned.png",
    }

    # Confirm that the fake client was created and used
    assert clients and clients[0].models.calls and len(clients[0].models.calls) == 2
    assert all(call["model"] == "gemini-3-pro-image-preview" for call in clients[0].models.calls)

    # Confirm the fake responses that were used all reported status 200
    assert all(r.status_code == 200 for r in responses)

# Test cases for clean_frames function
def test_clean_frames_requires_existing_input_dir(tmp_path, monkeypatch):
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    api_call, _ = load_api_call_with_fakes(monkeypatch, [])

    with pytest.raises(ValueError):
        api_call.clean_frames("key", str(tmp_path / "missing"), str(results_dir))

# Test cases for clean_frames function
def test_clean_frames_requires_results_dir_directory(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    bad_results = tmp_path / "results.txt"
    bad_results.write_text("not a dir")

    api_call, _ = load_api_call_with_fakes(monkeypatch, [])

    with pytest.raises(ValueError):
        api_call.clean_frames("key", str(input_dir), str(bad_results))

# Test cases for clean_frames function
def test_clean_frames_raises_on_bad_status(tmp_path, monkeypatch):
    input_dir = tmp_path / "input"
    results_dir = tmp_path / "results"
    input_dir.mkdir()
    results_dir.mkdir()

    Image.new("RGB", (5, 5)).save(input_dir / "frame.png")

    responses = [FakeResponse([], status_code=500)]
    api_call, _ = load_api_call_with_fakes(monkeypatch, responses)

    with pytest.raises(RuntimeError):
        api_call.clean_frames("key", str(input_dir), str(results_dir))


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
