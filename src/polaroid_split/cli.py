"""Command-line entry point and independent per-file batch processing."""

import argparse
import math
import sys
from pathlib import Path

from .image_io import split_scan

EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}


def margin_value(value: str) -> float:
    try:
        number = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("margin must be a number") from error
    if not math.isfinite(number) or number < 0:
        raise argparse.ArgumentTypeError("margin must be finite and non-negative")
    return number


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Split Polaroid adapter scans into full-print PNGs."
    )
    parser.add_argument("input", type=Path, help="scan file or folder (non-recursive)")
    parser.add_argument("--output", type=Path, help="destination folder (default: split)")
    parser.add_argument(
        "--margin-mm",
        type=margin_value,
        default=0.5,
        help="outer buffer in millimetres per side (default: 0.5)",
    )
    args = parser.parse_args(argv)
    source = args.input.expanduser()
    if not source.exists():
        parser.error(f"input does not exist: {source}")
    if source.is_dir():
        files = sorted(
            path
            for path in source.iterdir()
            if path.is_file() and path.suffix.lower() in EXTENSIONS
        )
        default_output = source / "split"
    elif source.is_file() and source.suffix.lower() in EXTENSIONS:
        files = [source]
        default_output = source.parent / "split"
    else:
        parser.error("input must be a JPEG, PNG, TIFF file or a directory")
    output = args.output.expanduser() if args.output else default_output
    if output.exists() and not output.is_dir():
        parser.error("output must be a directory")
    if source.is_dir() and output.resolve() == source.resolve():
        parser.error("output must differ from the input folder to avoid reprocessing crops")
    if not files:
        print("No supported scan files found.")
        return 0
    failed = False
    for path in files:
        try:
            destinations, empty = split_scan(path, output, args.margin_mm)
            result = f"exported {len(destinations)} PNGs" if destinations else "no prints found"
            skipped = f"; empty: {', '.join(empty)}" if empty else ""
            print(f"{path.name}: {result}{skipped}")
        except (OSError, ValueError, RuntimeError) as error:
            print(f"{path.name}: error: {error}", file=sys.stderr)
            failed = True
    return 1 if failed else 0
