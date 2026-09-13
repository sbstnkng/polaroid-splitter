"""Opt-in tests; no personal images are stored in the repository."""

import os
from pathlib import Path

import pytest
from PIL import Image

from polaroid_split.image_io import split_scan

SCAN_DIR = os.environ.get("POLAROID_SCAN_DIR")
pytestmark = pytest.mark.skipif(not SCAN_DIR, reason="set POLAROID_SCAN_DIR for private fixtures")


@pytest.mark.parametrize(
    "name,count",
    [
        ("full-1.jpg", 4),
        ("full-2.jpg", 4),
        ("full-color.jpg", 4),
        ("reversed-adapter.jpg", 4),
        ("partial.jpg", 2),
    ],
)
def test_reference_scan(name, count, tmp_path):
    paths, empty = split_scan(Path(SCAN_DIR) / name, tmp_path, 0.5)
    assert len(paths) == count
    if count == 2:
        assert empty == ["top-right", "bottom-left"]
    for path in paths:
        with Image.open(path) as image:
            assert 2000 < image.width < 2250
            assert 2450 < image.height < 2700
