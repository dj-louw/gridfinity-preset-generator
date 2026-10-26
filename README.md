# Gridfinity Preset Generator

Auto-generate a tree of easily navigable Gridfinity bins of various shapes and sizes and configurations, and slice the lot of them, and save them all on your printer. That way you have a list of all the bins you could possibly need, sliced and ready to go on your printer.

## Example output tree

```text
gridfinity-bins/
├── 1w/
│   ├── 1d/
│   │   ├── 3h/
│   │   │   ├── 1x1x3.stl
│   │   │   ├── 1x1x3-labeltab.stl
│   │   │   └── 1x1x3-fingerscoop.stl
│   │   └── 2d/
│   │       └── 6h/
│   │           └── 1x2x6.stl
│   └── 2w/
│       └── 1d/
│           └── 6h/
│               └── 2x1x6.stl
└── 3w/
    └── 3d/
        └── 7h/
            └── 3x3x7.stl
```

This repo also includes a script to generate Gridfinity rugged boxes, from the [monoscad project](https://github.com/smkent/monoscad), that saves a couple of common presets I use most often.

## Repository layout

- `generate_gridfinity_bins.py` — generates standard Gridfinity bin STL files
- `slice_gridfinity_bins.py` — slices generated bin STL files with OrcaSlicer
- `generate_rugged_box.py` — generates rugged box parts from a preset-based box model
- `gridfinity-bins/` — generated bin output tree
- `gridfinity-rugged-box/` — generated rugged box output tree
- `orca-settings/` — slicer preset JSON files used when slicing bins
- `gridfinity-rebuilt-openscad/` — source Gridfinity bin model
- `monoscad/` — source monoscad models and libraries

## Scripts

### `generate_gridfinity_bins.py`

This script generates a library of Gridfinity bin STL files from the OpenSCAD model in `gridfinity-rebuilt-openscad/gridfinity-rebuilt-bins.scad`.

It creates files in a structured layout such as:

- `gridfinity-bins/1w/1d/3h/1x1x3.stl`
- `gridfinity-bins/2w/3d/6h/2x3x6.stl`

The script supports selecting width, depth, and height combinations and can generate variants with or without:

- label-tab features
- finger-scoop features

Typical usage:

```bash
python3 generate_gridfinity_bins.py
python3 generate_gridfinity_bins.py --widths 1,2 --depths 1,2 --heights 3,6
python3 generate_gridfinity_bins.py --output-root ./my-bin-library --force
```

Use this when you want a batch of standard Gridfinity bins ready to print or to feed into the slicer.

### `slice_gridfinity_bins.py`

This script walks the `gridfinity-bins/` tree, finds STL files, and slices them using OrcaSlicer with the repository-local settings in `orca-settings/`.

It loads the configured process, machine, and filament JSON files, then writes matching `.gcode` files next to the STL files.

Typical usage:

```bash
python3 slice_gridfinity_bins.py
python3 slice_gridfinity_bins.py --input-root ./gridfinity-bins --dry-run
python3 slice_gridfinity_bins.py --force
```

Use this when you have generated a batch of bin STLs and want them converted into print-ready G-code.

### `generate_rugged_box.py`

This script generates STL files for the rugged Gridfinity storage box model from `monoscad/gridfinity/rugged-box/rugged-box-gridfinity.scad`.

It is preset-based and can export a box as a set of individual parts such as:

- bottom
- top
- latch
- handle

The script includes built-in presets like `5x5-standard`, `wide`, and `5x5-double-depth-12`, and also allows per-run overrides for width, length, and height.

Typical usage:

```bash
python3 generate_rugged_box.py --preset default
python3 generate_rugged_box.py --preset wide --part bottom --part top
python3 generate_rugged_box.py --preset 5x5-double-depth-12 --output-root ./output
```

Use this when you want a rugged enclosure or box body assembled from separate printable parts.

## build_orca_settings.py

In order to use OrcaSlicer's CLI mode, we need to provide profile settings for the machine, filament and process. Exporting these settings from the sclicer is not enough as the format is not compatible. This script uses the paths defined in profile-paths.json to combine your selected custom process/filament/machine settings with whatever bases they are inheriting from. The resultant combination scripts can then be used to slice your bins. You might want to further tweak the settings, but you can do that then in the resultant json files and your setup in OrcaSlicer remains untouched.

## Getting up and running

Before the scripts will work correctly, you need to fetch the repository's Git submodules and run the setup steps for the embedded `monoscad` repo.

```bash
git clone --recurse-submodules <repo-url>
# or, if the repo was already cloned without submodules:
git submodule update --init --recursive
```

The `monoscad` directory includes a `mise.toml` file with a required post-install hook that initializes its own nested submodules and installs `prek`:

```bash
cd monoscad
mise install
```

This step is important: the `monoscad` setup hook runs:

```bash
git submodule update --init --recursive
prek install
```

Without this, the nested model dependencies and tooling may not be present, and the Gridfinity model generation scripts may fail.

After the submodules and `mise` setup are complete, verify the OpenSCAD dependency is available on your `PATH` and then run the generator scripts from the repository root:

```bash
python3 generate_gridfinity_bins.py
python3 generate_rugged_box.py --preset 5x5-standard
python3 slice_gridfinity_bins.py
```

## Requirements

- Python 3
- OpenSCAD installed and available on your PATH
- OrcaSlicer installed for G-code generation

The scripts automatically look for OpenSCAD (`openscad` or `openscad-nightly`) and will fail clearly if it is not installed.

## Acknowledgements

This project builds on the work of the upstream Gridfinity ecosystem and the authors of the bundled submodule repositories:

- `gridfinity-rebuilt-openscad` — Kenneth (Ken) and the Gridfinity Rebuilt community
- `monoscad` — the `monoscad` project authors and contributors
- Zach Freedman — original creator of Gridfinity

Without their original work and open-source contributions, this work would not be possible.
