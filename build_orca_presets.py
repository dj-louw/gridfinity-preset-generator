#!/usr/bin/env python3
"""Merge selected OrcaSlicer system presets with user overrides.

This script reads the repo-local `profile-paths.json` config, loads the matching
system and user preset JSON files, applies the user settings on top of the
system settings, and writes the merged result into a repo-local `presets/`
directory.

The resulting files are self-contained preset JSONs that can be passed directly
to OrcaSlicer via `--load-settings` / `--load-filaments`.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


CONFIG_PATH = Path(__file__).resolve().parent / "profile-paths.json"
OUTPUT_ROOT = Path(__file__).resolve().parent / "orca-settings"


def load_profile_paths(config_path: Path) -> dict[str, dict[str, str]]:
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {config_path}")

    for section in ("user", "system"):
        if section not in data:
            data[section] = {}
        if not isinstance(data[section], dict):
            raise ValueError(f"Expected {section} to be an object in {config_path}")

    return {"user": data.get("user", {}), "system": data.get("system", {})}


def deep_merge(base: Any, override: Any) -> Any:
    if isinstance(base, dict) and isinstance(override, dict):
        merged = deepcopy(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = deepcopy(value)
        return merged
    return deepcopy(override)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected an object in {path}, got {type(data).__name__}")
    return data


def merge_presets(base_path: Path, user_path: Path | None, output_path: Path) -> None:
    base = read_json(base_path)
    user = read_json(user_path) if user_path and user_path.exists() else {}
    merged = deep_merge(base, user)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent="\t")
        handle.write("\n")


def resolve_kind_paths(config_path: Path) -> dict[str, tuple[Path, Path | None, str]]:
    parsed = load_profile_paths(config_path)

    paths: dict[str, tuple[Path, Path | None, str]] = {}
    for kind in ("filament", "machine", "process"):
        system_value = parsed["system"].get(kind)
        user_value = parsed["user"].get(kind)
        if not system_value:
            raise ValueError(f"Missing system preset for {kind} in {config_path}")

        system_path = Path(system_value).expanduser()
        if not system_path.exists():
            raise FileNotFoundError(f"System preset not found for {kind}: {system_path}")

        user_path = Path(user_value).expanduser() if user_value else None
        output_name = f"{kind}.json"
        paths[kind] = (system_path, user_path, output_name)

    return paths


def main() -> int:
    profile_paths = resolve_kind_paths(CONFIG_PATH)

    for kind, (system_path, user_path, output_name) in profile_paths.items():
        output_path = OUTPUT_ROOT / output_name
        merge_presets(system_path, user_path, output_path)
        print(f"Wrote {kind}: {output_path}")

    print(f"Merged presets written to {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
