# Architecture

## Modules and data flow

1. `cli.py` parses arguments, validates paths, enumerates supported inputs, and
   processes files independently in a deterministic order.
2. `image_io.load_scan` opens a single-page image, applies EXIF display orientation,
   swaps DPI axes when needed, and checks the supported pixel mode.
3. `detection.detect` returns a typed `Slot` for each of four regions. A slot has
   a name, a `State` (`occupied`, `empty`, `uncertain`), and an optional bounding box.
4. `image_io.split_scan` rejects uncertainty, checks collisions, expands accepted
   boxes, stages PNGs, and publishes without overwriting.

Boxes use `(left, top, right, bottom)` in displayed source pixels. Right and bottom
are exclusive, matching Pillow crop semantics. No network service is involved.

## Detection

`Configuration` in `src/polaroid_split/detection.py` is the source of truth for
layout and tuning. Normalized regions account for the two calibrated adapter
placements. The logo is deliberately irrelevant to the algorithm.

The detector checks aspect ratio, reduces the image to at most 1275 pixels wide,
and thresholds each region using Otsu with a constrained threshold range. External
contours must match expected print width/height, rectangularity, and long outer
edge support. Dark photo content and handwriting can remain inside the contour.

A region without a print is empty only when bright coverage is low and significant
remaining contours are small and circular, like the adapter holes. Unrecognized
shapes and multiple print candidates are uncertain. This is a geometric heuristic,
not a learned or statistically calibrated confidence score.

Accepted reduced-resolution bounds are mapped outward to a padded source region.
The same contour checks then refine the bounds at full resolution. Axis-aligned
bounding boxes preserve minor skew without resampling the source photo.

## Margins and metadata

Each axis uses `ceil(margin_mm * dpi / 25.4)` pixels. Valid positive finite source
DPI takes precedence; otherwise dimensions relative to 5100 × 7016 at 600 DPI
provide the estimate. Bounds extending outside the source cause a failure.

PNG outputs retain ICC profiles and DPI. Crop metadata is cleared before saving
so old dimensions, orientation tags and thumbnails are not copied. EXIF orientation
is applied once when loading, independently of which way the print's scene faces.

## Publication and failures

All slot classifications, destinations and margins are checked before writing.
Each scan's PNGs are encoded in a temporary directory on the output filesystem.
Hard links publish them with atomic non-overwrite semantics per file. If publication
fails, already published outputs from this scan are removed and staging is cleaned.

The group of PNGs is not a filesystem transaction. A forced termination may leave
partial publication. The output filesystem must support hard links. Other scans
in a batch are independent, and original images are never written.

## Extension boundaries

Support for another framing should be based on representative measurements and
fixtures, not a larger aspect-ratio tolerance alone. Keep constants centralized,
exercise empty slots and both placements, and visually inspect borders. General
rotation, alternate film formats and colour correction are separate features.
