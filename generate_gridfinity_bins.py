#!/usr/bin/env python3
"""Generate Gridfinity bin STL files into a width/depth/height folder structure.

This script renders a small starter library of bins using the OpenSCAD model in
`gridfinity-rebuilt-openscad/gridfinity-rebuilt-bins.scad`.

Example:
    python3 generate_gridfinity_bins.py --widths 1,2 --depths 1,2 --heights 3,6

The default output root is the current working directory, producing paths such as:
    ./width/1w/depth/1d/height/3h/1x1x3.stl

Additional config variants can be added later without changing the folder layout:
    --configurations basic,label-tab,finger-scoop
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_WIDTHS = [1]
DEFAULT_DEPTHS = [1]
DEFAULT_HEIGHTS = [3,6,7]

# Values are 0=full, 1=auto, 2=left, 3=center, 4=right, 5=none.
LABELTAB_STYLE = 5

# A value of 0 disables the scoop; values between 0 and 1 scale the scoop amount.
FINGER_SCOOP_ENABLED = 0


def parse_csv_ints(raw: str) -> list[int]:
    values = []
    for token in raw.split(","):
        item = token.strip()
        if not item:
            continue
        try:
            values.append(int(item))
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"Invalid integer list entry: {item!r}") from exc
    if not values:
        raise argparse.ArgumentTypeError("At least one integer is required")
    return values


def find_openscad() -> str:
    candidates = [
        "openscad-nightly",
        "openscad",
        "/snap/bin/openscad-nightly",
        "/usr/bin/openscad",
        "/usr/local/bin/openscad",
    ]

    for candidate in candidates:
        path = shutil.which(candidate)
        if path:
            return path

        if candidate.startswith("/") and Path(candidate).exists() and Path(candidate).is_file():
            return candidate

    raise FileNotFoundError(
        "OpenSCAD is not installed or not on PATH. Install OpenSCAD or add openscad-nightly to PATH."
    )


def build_model_path(output_root: Path, width: int, depth: int, height: int) -> Path:
    return output_root / "gridfinity-bins" / f"{width}w" / f"{depth}d" / f"{height}h"


def feature_suffix(label_tab: bool, finger_scoop: bool) -> str:
    suffixes = []
    if label_tab:
        suffixes.append("labeltab")
    if finger_scoop:
        suffixes.append("fingerscoop")
    return ("-" + "-".join(suffixes)) if suffixes else ""


def build_output_filename(width: int, depth: int, height: int, label_tab: bool, finger_scoop: bool) -> str:
    suffix = feature_suffix(label_tab, finger_scoop)
    return f"{width}x{depth}x{height}{suffix}.stl"


def iter_variants(label_tab: bool | None = None, finger_scoop: bool | None = None) -> list[tuple[bool, bool]]:
    tab_enabled = LABELTAB_STYLE != 5
    scoop_enabled = FINGER_SCOOP_ENABLED != 0

    if label_tab is None and finger_scoop is None:
        variants = [(False, False)]
        if tab_enabled:
            variants.append((True, False))
        if scoop_enabled:
            variants.append((False, True))
        if tab_enabled and scoop_enabled:
            variants.append((True, True))
        return variants

    selected = []
    if label_tab is not None:
        selected.append(label_tab)
    else:
        selected.append(False)
    if finger_scoop is not None:
        selected.append(finger_scoop)
    else:
        selected.append(False)

    if selected == [True, False]:
        return [(True, False)]
    if selected == [False, True]:
        return [(False, True)]
    if selected == [True, True]:
        return [(True, True)]
    return [(False, False)]


def render_bin(scad_path: Path, output_path: Path, width: int, depth: int, height: int, label_tab: bool, finger_scoop: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    style_tab = LABELTAB_STYLE if label_tab and LABELTAB_STYLE != 5 else 5
    scoop_value = FINGER_SCOOP_ENABLED if finger_scoop and FINGER_SCOOP_ENABLED != 0 else 0

    args = [
        find_openscad(),
        "-o",
        str(output_path),
        "-D",
        f"gridx={width}",
        "-D",
        f"gridy={depth}",
        "-D",
        f"gridz={height}",
        "-D",
        f"style_tab={style_tab}",
        "-D",
        f"scoop={scoop_value}",
    ]

    args.append(str(scad_path))

    print("$", " ".join(args))
    subprocess.run(args, check=True)


def run_generation(
    output_root: Path,
    widths: list[int],
    depths: list[int],
    heights: list[int],
    dry_run: bool,
    force: bool,
    label_tab: bool | None,
    finger_scoop: bool | None,
) -> int:
    repo_root = Path(__file__).resolve().parent
    scad_path = repo_root / "gridfinity-rebuilt-openscad" / "gridfinity-rebuilt-bins.scad"

    if not scad_path.exists():
        raise FileNotFoundError(f"Model not found: {scad_path}")

    variants = iter_variants(label_tab=label_tab, finger_scoop=finger_scoop)
    generated = 0
    total = len(widths) * len(depths) * len(heights) * len(variants)

    for width in widths:
        for depth in depths:
            for height in heights:
                for label_tab_enabled, finger_scoop_enabled in variants:
                    folder = build_model_path(output_root, width, depth, height)
                    filename = build_output_filename(width, depth, height, label_tab_enabled, finger_scoop_enabled)
                    output_path = folder / filename

                    if output_path.exists() and not force:
                        print(f"Skipping existing file: {output_path}")
                        continue

                    if dry_run:
                        print(f"Would generate: {output_path}")
                        generated += 1
                        continue

                    render_bin(scad_path, output_path, width, depth, height, label_tab_enabled, finger_scoop_enabled)
                    generated += 1

    print(f"Completed: {generated}/{total} files generated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate a Gridfinity bin STL library from the OpenSCAD submodule."
    )
    parser.add_argument(
        "--widths",
        type=parse_csv_ints,
        default=DEFAULT_WIDTHS,
        help="Comma-separated widths (for example: 1,2,3)",
    )
    parser.add_argument(
        "--depths",
        type=parse_csv_ints,
        default=DEFAULT_DEPTHS,
        help="Comma-separated depths (for example: 1,2,3)",
    )
    parser.add_argument(
        "--heights",
        type=parse_csv_ints,
        default=DEFAULT_HEIGHTS,
        help="Comma-separated heights (for example: 3,6)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd(),
        help="Root directory where the width/depth/height structure will be created",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generation actions without writing any STL files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files if they already exist",
    )
    parser.add_argument(
        "--label-tab",
        action="store_true",
        help="Generate label-tab variants only. If omitted, all variants are generated.",
    )
    parser.add_argument(
        "--finger-scoop",
        action="store_true",
        help="Generate finger-scoop variants only. If omitted, all variants are generated.",
    )
    args = parser.parse_args()

    try:
        label_tab_flag = True if args.label_tab else None
        finger_scoop_flag = True if args.finger_scoop else None

        return run_generation(
            output_root=args.output_root,
            widths=args.widths,
            depths=args.depths,
            heights=args.heights,
            dry_run=args.dry_run,
            force=args.force,
            label_tab=label_tab_flag,
            finger_scoop=finger_scoop_flag,
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"OpenSCAD failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
