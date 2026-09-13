# Contributor and agent guidance

## Purpose

Maintain a small local CLI for standardized four-slot Polaroid adapter scans.
Preserve complete white print borders, handwriting, colour and pixel resolution.
This is a calibrated splitter, not a general scanner application or photo editor.

## Start here

Read `README.md`, `docs/architecture.md`, and `docs/development.md` before changes.
Use Python 3.11+ and uv. The command is `polaroid-split`, the Python package is
`polaroid_split`, and the GitHub repository is `polaroid-splitter`.

```sh
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

## Architecture and invariants

- `detection.py`: normalized regions, shared thresholds, slot classification,
  and full-resolution refinement.
- `image_io.py`: EXIF display orientation, DPI/profile handling, margin expansion,
  staging, and non-overwriting output publication.
- `cli.py`: arguments, deterministic non-recursive batches, and reporting.
- Keep tuning constants in `Configuration`. Never add per-file exceptions.
- Either supported adapter placement must work without rotating photo content.
- Circular holes are not prints. An uncertain slot rejects the entire scan.
- Never modify sources or overwrite outputs. Preserve ICC/DPI and decoded crop
  pixels. Do not copy stale EXIF or thumbnails into outputs.

## Code and validation

Write idiomatic, typed Python with focused functions and meaningful names. Follow
Ruff rules and keep dependencies small. Add tests for meaningful behaviour changes.
Use synthetic images in committed tests. Optional real-scan tests are described
in the development guide and must remain opt-in. For detection changes, visually
check complete borders and buffers with both adapter placements and empty slots.
Update documentation whenever behaviour or installation changes.

## Public repository hygiene

Never commit personal photographs, generated crops, real scan names, local paths,
credentials, private account information, conversation logs or machine-specific
agent/memory instructions. Use generic fixture names and examples. Review the
staged file list and diff before publishing; ignore rules are only a backstop.
Do not introduce a license or change licensing terms without the owner's choice.
