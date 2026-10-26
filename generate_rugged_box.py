#!/usr/bin/env python3
"""Generate rugged Gridfinity storage box STL files from the monoscad submodule.

This script renders one or more individual parts from the OpenSCAD model in
`monoscad/gridfinity/rugged-box/rugged-box-gridfinity.scad`.

The preset values and export parts are all defined near the top of this file so
that they can be adjusted without editing the logic below.

Examples:
    python3 generate_rugged_box.py --preset default
    python3 generate_rugged_box.py --preset my-favourite --part bottom --part top
    python3 generate_rugged_box.py --width 4 --length 3 --bottom-height 7 --top-height 2
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# -----------------------------------------------------------------------------
# User-editable configuration
# -----------------------------------------------------------------------------

# Default preset to render when none is supplied on the command line.
DEFAULT_PRESET = "default"

# Saved presets. Update these with the dimensions you use most often.
PRESETS: dict[str, dict[str, Any]] = {
    "default": {
        "Width": 4,
        "Length": 2,
        "Bottom_Height": 7,
        "Top_Height": 2,
    },
    "small": {
        "Width": 2,
        "Length": 2,
        "Bottom_Height": 4,
        "Top_Height": 2,
    },
    "standard": {
        "Width": 4,
        "Length": 3,
        "Bottom_Height": 7,
        "Top_Height": 2,
    },
    "wide": {
        "Width": 6,
        "Length": 4,
        "Bottom_Height": 7,
        "Top_Height": 2,
    },
}

# Set the specific box part(s) to render. For a slicer-friendly workflow, keep
# this as a list of the individual printable parts rather than the combined
# assembled preview.
PARTS_TO_EXPORT = [
    "bottom",
    "top",
    "latch",
    "stacking_latch",
    "handle",
    "label",
]

# Optional global Top/Bottom values that apply to all presets unless overridden.
BASE_SETTINGS: dict[str, Any] = {
    "Gridfinity_Base_Style": "enabled",
    "Gridfinity_Stackable": True,
    "Lip_Seal_Type": "wedge",
    "Reinforced_Corners": True,
    "Top_Grip": True,
    "Hinge_End_Stops": True,
    "Stacking_Latches": True,
    "Latch_Type": "draw",
    "Third_Hinge": True,
    "Handle": True,
    "Label": True,
    "Label_Text": "Label",
    "Label_Text_Size": 10,
    "Wall_Thickness": 3.0,
    "Lip_Thickness": 3.0,
    "Rib_Width": 6,
    "Latch_Width": 28,
    "Latch_Screw_Separation": 16,
    "Size_Tolerance": 0.20,
}

# -----------------------------------------------------------------------------
# Generation utilities
# -----------------------------------------------------------------------------


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


def openscad_arg_list(params: dict[str, Any]) -> list[str]:
    """Convert a dict of SCAD param names and values into OpenSCAD -D args."""
    args: list[str] = []
    for key, value in params.items():
        if isinstance(value, str):
            literal = f'"{value}"'
            args.extend(["-D", f"{key}={literal}"])
        elif isinstance(value, bool):
            args.extend(["-D", f"{key}={'true' if value else 'false'}"])
        else:
            args.extend(["-D", f"{key}={value}"])
    return args


def scad_model_path() -> Path:
    repo_root = Path(__file__).resolve().parent
    model = repo_root / "monoscad" / "gridfinity" / "rugged-box" / "rugged-box-gridfinity.scad"
    if not model.exists():
        raise FileNotFoundError(f"Model not found: {model}")
    return model


def preset_config(preset_name: str, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    preset_name = preset_name or DEFAULT_PRESET
    if preset_name not in PRESETS:
        available = ", ".join(sorted(PRESETS))
        raise ValueError(f"Unknown preset {preset_name!r}. Available presets: {available}")

    config: dict[str, Any] = {**BASE_SETTINGS, **PRESETS[preset_name]}
    if overrides:
        config.update(overrides)
    return config


def output_dir_for_preset(output_root: Path, preset_name: str, width: int, length: int, bottom_height: int, top_height: int) -> Path:
    folder_name = f"{width}w-{length}d-{bottom_height}bh-{top_height}th"
    return output_root / "rugged-box" / preset_name / folder_name


def render_part(
    scad_path: Path,
    output_path: Path,
    part_name: str,
    params: dict[str, Any],
    force: bool,
    dry_run: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists() and not force:
        print(f"Skipping existing file: {output_path}")
        return

    if dry_run:
        print(f"Would generate: {output_path} ({part_name})")
        return

    args = [
        find_openscad(),
        "-o",
        str(output_path),
        *openscad_arg_list({**params, "Part": part_name}),
        str(scad_path),
    ]

    print("$", " ".join(args))
    subprocess.run(args, check=True)


def generate_box(
    preset_name: str,
    output_root: Path,
    part_names: list[str] | None,
    override_values: dict[str, Any],
    force: bool,
    dry_run: bool,
) -> int:
    config = preset_config(preset_name, overrides=override_values)
    if not part_names:
        part_names = list(PARTS_TO_EXPORT)

    width = int(config["Width"])
    length = int(config["Length"])
    bottom_height = int(config["Bottom_Height"])
    top_height = int(config["Top_Height"])

    scad_path = scad_model_path()
    preset_dir = output_dir_for_preset(output_root, preset_name, width, length, bottom_height, top_height)

    generated = 0
    for part_name in part_names:
        output_path = preset_dir / f"{part_name}.stl"
        render_part(scad_path, output_path, part_name, config, force, dry_run)
        generated += 1

    print(f"Preset {preset_name!r} -> generated {generated} STL files in {preset_dir}")
    return 0


def parse_part_names(raw_parts: list[str]) -> list[str]:
    if not raw_parts:
        return list(PARTS_TO_EXPORT)

    normalized = []
    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        normalized.append(part)
    if not normalized:
        return list(PARTS_TO_EXPORT)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate individual STL parts for the monoscad rugged Gridfinity box."
    )
    parser.add_argument(
        "--preset",
        default=DEFAULT_PRESET,
        help=f"Preset name to render. Available: {', '.join(sorted(PRESETS))}",
    )
    parser.add_argument(
        "--part",
        action="append",
        dest="parts",
        default=[],
        help="One or more part names to export (for example: bottom top latch). Repeat the flag as needed.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path.cwd(),
        help="Directory where generated STL files will be saved.",
    )
    parser.add_argument("--width", type=int, help="Override preset width in Gridfinity units")
    parser.add_argument("--length", type=int, help="Override preset length in Gridfinity units")
    parser.add_argument("--bottom-height", type=int, help="Override preset bottom height in 7mm units")
    parser.add_argument("--top-height", type=int, help="Override preset top height in 7mm units")
    parser.add_argument("--dry-run", action="store_true", help="Print intended generation without writing any files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files when they already exist")
    args = parser.parse_args()

    override_values: dict[str, Any] = {}
    if args.width is not None:
        override_values["Width"] = args.width
    if args.length is not None:
        override_values["Length"] = args.length
    if args.bottom_height is not None:
        override_values["Bottom_Height"] = args.bottom_height
    if args.top_height is not None:
        override_values["Top_Height"] = args.top_height

    try:
        return generate_box(
            preset_name=args.preset,
            output_root=args.output_root,
            part_names=parse_part_names(args.parts),
            override_values=override_values,
            force=args.force,
            dry_run=args.dry_run,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        print(f"OpenSCAD failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
