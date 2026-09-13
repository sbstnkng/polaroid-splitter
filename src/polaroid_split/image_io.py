"""Image loading, metadata handling and non-overwriting output publication."""

import math
import os
import tempfile
from pathlib import Path

from PIL import Image, ImageOps

from .detection import CONFIG, Box, State, detect


def effective_dpi(image: Image.Image) -> tuple[float, float]:
    dpi = image.info.get("dpi")
    if isinstance(dpi, (tuple, list)) and len(dpi) == 2:
        try:
            values = tuple(float(value) for value in dpi)
            if all(math.isfinite(value) and value > 0 for value in values):
                return values
        except (TypeError, ValueError):
            pass
    return (
        image.width / CONFIG.reference_width * CONFIG.reference_dpi,
        image.height / CONFIG.reference_height * CONFIG.reference_dpi,
    )


def expand_box(box: Box, margin_mm: float, dpi: tuple[float, float], size: tuple[int, int]) -> Box:
    if not math.isfinite(margin_mm) or margin_mm < 0:
        raise ValueError("margin must be a finite, non-negative number")
    dx, dy = (math.ceil(margin_mm * value / 25.4) for value in dpi)
    left, top, right, bottom = box
    expanded = (left - dx, top - dy, right + dx, bottom + dy)
    if expanded[0] < 0 or expanded[1] < 0 or expanded[2] > size[0] or expanded[3] > size[1]:
        raise ValueError("requested margin extends beyond the scan")
    return expanded


def load_scan(path: Path) -> Image.Image:
    with Image.open(path) as source:
        if getattr(source, "n_frames", 1) != 1:
            raise ValueError("multi-page images are unsupported; export each page separately")
        orientation = source.getexif().get(274, 1)
        image = ImageOps.exif_transpose(source)
        if orientation in (5, 6, 7, 8) and "dpi" in image.info:
            image.info["dpi"] = tuple(reversed(image.info["dpi"]))
        image.load()
    if image.mode not in ("L", "RGB", "RGBA"):
        raise ValueError(f"unsupported image mode {image.mode}; use an RGB or grayscale scan")
    return image


def split_scan(source: Path, output: Path, margin_mm: float) -> tuple[list[Path], list[str]]:
    with load_scan(source) as image:
        slots = detect(image)
        uncertain = [slot.name for slot in slots if slot.state == State.UNCERTAIN]
        if uncertain:
            raise ValueError("uncertain detection in " + ", ".join(uncertain))
        occupied = [slot for slot in slots if slot.state == State.OCCUPIED]
        empty = [slot.name for slot in slots if slot.state == State.EMPTY]
        if not occupied:
            return [], empty
        destinations = [
            output / f"{source.stem}_{source.suffix[1:].lower()}_{slot.name}.png"
            for slot in occupied
        ]
        for destination in destinations:
            if destination.exists() or destination.is_symlink():
                raise FileExistsError(f"output already exists: {destination}")
        dpi = effective_dpi(image)
        boxes = [expand_box(slot.box, margin_mm, dpi, image.size) for slot in occupied]
        output.mkdir(parents=True, exist_ok=True)
        published = []
        # Stage on the destination filesystem; hard links publish without overwriting.
        with tempfile.TemporaryDirectory(prefix=".polaroid-split-", dir=output) as temporary:
            staged = []
            try:
                for index, box in enumerate(boxes):
                    path = Path(temporary) / f"{index}.png"
                    with image.crop(box) as crop:
                        crop.info.clear()
                        crop.save(
                            path, format="PNG", dpi=dpi, icc_profile=image.info.get("icc_profile")
                        )
                    staged.append(path)
                for path, destination in zip(staged, destinations, strict=True):
                    os.link(path, destination)
                    published.append(destination)
            except Exception:
                for destination in published:
                    destination.unlink()
                raise
        return destinations, empty
