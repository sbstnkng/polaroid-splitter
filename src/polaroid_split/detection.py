"""Layout-guided print detection; coordinates are exclusive on right/bottom."""

from dataclasses import dataclass
from enum import StrEnum

import cv2
import numpy as np
from PIL import Image

Box = tuple[int, int, int, int]


@dataclass(frozen=True)
class Configuration:
    reference_width: int = 5100
    reference_height: int = 7016
    reference_dpi: int = 600
    detection_width: int = 1275
    aspect_tolerance: float = 0.025
    threshold_floor: int = 90
    threshold_ceiling: int = 160
    minimum_rectangularity: float = 0.90
    minimum_edge_support: float = 0.75
    width_range: tuple[float, float] = (0.36, 0.45)
    height_range: tuple[float, float] = (0.32, 0.40)
    empty_bright_fraction: float = 0.15
    hole_max_width: float = 0.13
    hole_max_height: float = 0.10
    hole_min_circularity: float = 0.65
    noise_area_fraction: float = 0.0001
    refinement_padding: float = 0.004
    regions: tuple[tuple[str, tuple[float, float, float, float]], ...] = (
        ("top-left", (0.04, 0.035, 0.49, 0.44)),
        ("top-right", (0.51, 0.035, 0.96, 0.44)),
        ("bottom-left", (0.04, 0.44, 0.49, 0.835)),
        ("bottom-right", (0.51, 0.44, 0.96, 0.835)),
    )


CONFIG = Configuration()


class State(StrEnum):
    OCCUPIED = "occupied"
    EMPTY = "empty"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True)
class Slot:
    name: str
    state: State
    box: Box | None = None


def _mask(gray: np.ndarray, config: Configuration) -> np.ndarray:
    threshold, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    threshold = float(np.clip(threshold, config.threshold_floor, config.threshold_ceiling))
    return cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)[1]


def _contours(mask: np.ndarray) -> tuple:
    return cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]


def _is_print(contour: np.ndarray, width: int, height: int, config: Configuration) -> bool:
    _, _, w, h = cv2.boundingRect(contour)
    if not (
        config.width_range[0] <= w / width <= config.width_range[1]
        and config.height_range[0] <= h / height <= config.height_range[1]
    ):
        return False
    if cv2.contourArea(contour) / (w * h) < config.minimum_rectangularity:
        return False
    # A rectangle must have long supporting edges, not just a large bright blob.
    points = contour[:, 0, :]
    x, y = points.min(axis=0)
    tolerance = max(2, round(min(w, h) * 0.015))
    for axis, edge, length in ((0, x, h), (0, x + w - 1, h), (1, y, w), (1, y + h - 1, w)):
        edge_points = points[np.abs(points[:, axis] - edge) <= tolerance, 1 - axis]
        if len(edge_points) < 2 or np.ptp(edge_points) / length < config.minimum_edge_support:
            return False
    return True


def _is_empty(
    mask: np.ndarray, contours: tuple, width: int, height: int, config: Configuration
) -> bool:
    if np.count_nonzero(mask) / mask.size > config.empty_bright_fraction:
        return False
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < width * height * config.noise_area_fraction:
            continue
        _, _, w, h = cv2.boundingRect(contour)
        perimeter = cv2.arcLength(contour, True)
        circularity = 4 * np.pi * area / perimeter**2 if perimeter else 0
        if (
            w / width > config.hole_max_width
            or h / height > config.hole_max_height
            or circularity < config.hole_min_circularity
        ):
            return False
    return True


def detect(image: Image.Image, config: Configuration = CONFIG) -> list[Slot]:
    """Find each full print, leaving ambiguous slots explicitly unresolved."""
    width, height = image.size
    aspect = config.reference_width / config.reference_height
    if abs((width / height) / aspect - 1) > config.aspect_tolerance:
        raise ValueError("unsupported scan framing; use the full-bed portrait scan area")
    small_width = min(width, config.detection_width)
    small_height = round(height * small_width / width)
    gray = np.asarray(image.convert("L").resize((small_width, small_height)))
    full_gray = np.asarray(image.convert("L"))
    slots = []
    for name, region in config.regions:
        x0, y0, x1, y1 = (
            round(region[0] * small_width),
            round(region[1] * small_height),
            round(region[2] * small_width),
            round(region[3] * small_height),
        )
        mask = _mask(gray[y0:y1, x0:x1], config)
        contours = _contours(mask)
        candidates = [c for c in contours if _is_print(c, small_width, small_height, config)]
        if not candidates:
            state = (
                State.EMPTY
                if _is_empty(mask, contours, small_width, small_height, config)
                else State.UNCERTAIN
            )
            slots.append(Slot(name, state))
            continue
        if len(candidates) != 1:
            slots.append(Slot(name, State.UNCERTAIN))
            continue
        x, y, w, h = cv2.boundingRect(candidates[0])
        padding = round(width * config.refinement_padding)
        left = max(0, int((x + x0) * width / small_width) - padding)
        top = max(0, int((y + y0) * height / small_height) - padding)
        right = min(width, int(np.ceil((x + x0 + w) * width / small_width)) + padding)
        bottom = min(height, int(np.ceil((y + y0 + h) * height / small_height)) + padding)
        refined = _contours(_mask(full_gray[top:bottom, left:right], config))
        refined = [c for c in refined if _is_print(c, width, height, config)]
        if len(refined) != 1:
            slots.append(Slot(name, State.UNCERTAIN))
            continue
        x, y, w, h = cv2.boundingRect(refined[0])
        slots.append(Slot(name, State.OCCUPIED, (left + x, top + y, left + x + w, top + y + h)))
    return slots
