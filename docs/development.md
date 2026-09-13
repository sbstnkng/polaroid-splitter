# Development and testing

## Setup

```sh
git clone https://github.com/sbstnkng/polaroid-splitter.git
cd polaroid-splitter
uv sync --locked
uv run polaroid-split --help
```

Python 3.11+ is supported by the package metadata. Commit `uv.lock` when dependency
changes are intentional. The editable checkout uses `src/polaroid_split`; package
builds use Hatchling. A user installation is separate from the editable environment.

## Required checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Default tests generate synthetic white frames, dark photo interiors, handwriting,
and circular adapter holes. They cover occupancy, placement shifts, scaling,
uncertainty, crop pixels, metadata, EXIF orientation, invalid margins, corrupt input,
multi-page TIFFs, output conflicts, rollback, and non-recursive batch continuation.
Optional real-image cases are skipped unless the environment variable below is set.

## Optional real-scan validation

Keep photographs in a directory outside this repository. Prepare copies with the
following generic filenames; do not rename or modify your originals:

| Filename | Expected content |
| --- | --- |
| `full-1.jpg` | Four white-bordered prints |
| `full-2.jpg` | Four different white-bordered prints |
| `full-color.jpg` | Four colour photographs in white frames |
| `reversed-adapter.jpg` | Four prints with the adapter reversed 180 degrees |
| `partial.jpg` | Prints only in top-left and bottom-right |

These tests expect the reference 5100 × 7016 resolution at 600 DPI. They check
counts, empty slot positions and output dimension ranges, not visual correctness.

```sh
POLAROID_SCAN_DIR="/path/to/private-fixtures" uv run pytest tests/test_real_scans.py
```

After detection changes, manually inspect all crops: every corner, the entire
white border, handwriting, and the intended outside buffer must remain visible.
Also check that colours and photo orientation are unchanged and holes are excluded.
Never commit test photos, resulting PNGs, or diagnostic contact sheets.

## Making changes

Keep CLI, detection and I/O responsibilities separate. Add focused regression tests
for actual failure modes, and document behaviour changes. Run both file and folder
commands after changes to packaging or argument handling. Use a fresh output folder
for repeated manual tests because existing crops are intentionally not overwritten.

Before publishing, inspect `git diff --cached` and `git diff --cached --name-only`.
Use generic paths in examples. Confirm that private data, environment files,
credentials and personal commit email addresses are not being published. Ignore
rules help prevent accidents but can be overridden and do not replace review.

No license has been selected for this repository; public visibility alone does not
supply an open-source license. A licensing decision belongs to the repository owner.
