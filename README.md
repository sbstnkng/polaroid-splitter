# Polaroid Splitter

A small, local command-line tool that splits a four-slot Polaroid Film Scan Adapter
scan into individual PNGs. It keeps each complete white frame and handwriting,
with a small outer buffer, and skips empty slots.

**Designed for a fixed scanner setup.** The current detector is calibrated for
white-bordered i-Type prints in the layout described below. It is not a general
photo detector. Processing runs locally; the CLI does not upload your images.

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/). Developed and tested on
macOS; other operating systems have not been validated.

```sh
git clone https://github.com/sbstnkng/polaroid-splitter.git
cd polaroid-splitter
uv sync --locked
uv tool install .
polaroid-split --help
```

If the command is not found, run `uv tool update-shell` and open a new terminal.
You can also run it directly from the checkout using `uv run polaroid-split`.
The repository name is `polaroid-splitter`; the installed command is `polaroid-split`.

To update an existing installation, pull the latest checkout and run
`uv tool install --reinstall .`. Development uses `uv.lock` for repeatable installs;
`uv tool install .` resolves the package's declared dependency ranges separately.

## Usage

```sh
# One scan; writes into a sibling split folder.
polaroid-split "/path/to/scan.jpg"

# All supported files in one folder, without descending into subfolders.
polaroid-split "/path/to/photo scans"

# Choose an output directory or change the outer buffer.
polaroid-split "/path/to/photo scans" --output "/path/to/split photos"
polaroid-split "/path/to/scan.jpg" --margin-mm 1
polaroid-split "/path/to/scan.jpg" --margin-mm 0
```

| Argument | Behaviour |
| --- | --- |
| `input` | One JPEG, PNG, single-page TIFF, or a directory of scans |
| `--output PATH` | Output directory; defaults to `split` beside a file or inside the input directory |
| `--margin-mm NUMBER` | Non-negative outer margin per side; default `0.5` mm |
| `--help` | Show command help |

File extensions are case-insensitive. RGB, RGBA and grayscale images are accepted.
Batches run in filename order. Use an output directory separate from the input
folder so exports are not picked up as scans on later runs.

## Scanner setup

The supported framing is a portrait full-bed scan of **5100 × 7016 pixels at
600 DPI**, or the same framing at a proportionally scaled resolution. Calibration
used an HP ENVY Photo 6232 and white-bordered i-Type prints in the four-slot adapter.
Matching dimensions alone do not guarantee matching physical placement.

- Keep the adapter at the same position and preserve the full scan area.
- Place prints in a two-by-two layout. One to four prints, or an empty adapter,
  are supported.
- Both observed 180-degree adapter placements are accommodated. There is no logo
  recognition and no automatic photo-content rotation.
- Disable scanner auto-cropping. Arbitrary rotation, substantial movement, different
  film sizes, and coloured or black print borders are outside the current scope.

Approximate print bounds as percentages of the full image help identify whether
your setup matches:

| Slot | Left–right | Top–bottom |
| --- | --- | --- |
| Top-left | 7–48% | 6–43% |
| Top-right | 52–94% | 6–43% |
| Bottom-left | 7–48% | 45–83% |
| Bottom-right | 52–94% | 45–83% |

These are placement guides, not fixed crop coordinates. The tool finds each
print's actual outer edges inside broader search regions. Different framing
requires code-level calibration; there is no interactive calibration interface.

## Output and preservation

For `scan.jpg`, outputs are named:

```text
split/
  scan_jpg_top-left.png
  scan_jpg_top-right.png
  scan_jpg_bottom-left.png
  scan_jpg_bottom-right.png
```

Only occupied slots are exported. Slot names describe the input as displayed,
regardless of adapter orientation. The source extension is part of the filename
to distinguish inputs such as `scan.jpg` and `scan.png`.

- Original scans are never modified; existing outputs are never overwritten.
- A 0.5 mm margin is 12 pixels per side at 600 DPI and leaves a thin strip of adapter.
- Crops retain source resolution and decoded pixels. PNG introduces no further
  lossy compression, but cannot undo existing JPEG compression.
- Embedded ICC profiles and valid DPI are retained. Missing/invalid DPI is inferred
  from the reference scan dimensions. PNG DPI values can have small rounding differences.
- EXIF display orientation is applied. No additional rotation, resizing, deskewing,
  sharpening or colour correction is performed. Stale EXIF and thumbnails are omitted.

## Errors and troubleshooting

| Message or symptom | Action |
| --- | --- |
| Unsupported scan framing | Restore the full-bed portrait scan area and check adapter placement |
| Uncertain detection in a slot | Check that complete white borders are visible and the scan matches the expected layout |
| Output already exists | Choose a different output directory or move the previous exports yourself |
| Margin extends beyond the scan | Reduce the margin or rescan with sufficient surrounding area |
| Multi-page image unsupported | Export each page as a separate scan |
| Unsupported image mode | Export an RGB or grayscale scan |
| No prints found | All slots were classified as empty; if prints are present, check framing and border compatibility |

An uncertain slot causes that entire scan to be skipped. A failed scan does not
stop the rest of a batch. Output files are staged first and cleaned up on handled
publication failures. Forced process termination can leave temporary files or a
partially published scan; inspect the output directory before retrying.

Exit codes: **0** successful processing (including empty input folders or adapters),
**1** one or more processing failures, **2** invalid command usage.

## Development and documentation

```sh
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

- [Architecture and detection](docs/architecture.md)
- [Development, tests and optional local fixtures](docs/development.md)
- [Contributor and agent guidance](AGENTS.md)

The initial implementation was checked against five local scans yielding 18 crops,
including an inverted adapter and two empty slots. Those private images are not
included; default tests generate synthetic fixtures. This validation does not
establish compatibility with every scanner or adapter placement.

When reporting a bug, include the command, error message, image dimensions and
DPI, and runtime versions. Use synthetic or non-sensitive examples; do not post
private photographs, credentials, or machine-specific paths in public issues.

This independent project is not affiliated with or endorsed by Polaroid or HP.
