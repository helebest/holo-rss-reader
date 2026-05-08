"""Synchronize generated local plugin skills from the canonical skills directory."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .validate import PLUGIN_NAME, PLUGIN_ROOT, PLUGIN_SKILLS_DIR, SKILLS_DIR, validate_all

EXCLUDE_NAMES = {
    ".env",
    ".pytest_cache",
    ".venv",
    "__pycache__",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


class PluginSyncError(Exception):
    """Raised when the generated plugin skill copy is out of sync."""


def should_exclude(path: Path) -> bool:
    return path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES


def ignore_generated(_directory: str, names: list[str]) -> set[str]:
    return {name for name in names if should_exclude(Path(name))}


def sync_plugin_skills(destination: Path = PLUGIN_SKILLS_DIR) -> Path:
    """Replace the generated plugin skills directory from canonical skills."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(SKILLS_DIR, destination, ignore=ignore_generated)
    return destination


def iter_relative_files(root: Path) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(should_exclude(Path(part)) for part in relative.parts):
            continue
        if path.is_file():
            files[relative] = path
    return files


def compare_skill_trees(
    source: Path = SKILLS_DIR,
    destination: Path = PLUGIN_SKILLS_DIR,
) -> list[str]:
    """Return human-readable differences between two skill trees."""
    if not destination.exists():
        return [f"missing generated skills directory: {destination}"]

    differences: list[str] = []
    source_files = iter_relative_files(source)
    destination_files = iter_relative_files(destination)

    for relative in sorted(source_files.keys() - destination_files.keys()):
        differences.append(f"missing from generated copy: {relative.as_posix()}")
    for relative in sorted(destination_files.keys() - source_files.keys()):
        differences.append(f"extra in generated copy: {relative.as_posix()}")
    for relative in sorted(source_files.keys() & destination_files.keys()):
        if source_files[relative].read_bytes() != destination_files[relative].read_bytes():
            differences.append(f"content differs: {relative.as_posix()}")
    return differences


def check_plugin_layout() -> list[str]:
    """Validate tracked plugin metadata and any existing generated skills copy."""
    validate_all()
    if not PLUGIN_ROOT.exists():
        return [f"missing plugin root: {PLUGIN_ROOT}"]
    if not PLUGIN_SKILLS_DIR.exists():
        return []
    return compare_skill_trees()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"Synchronize generated skills for the {PLUGIN_NAME} local plugin."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate plugin metadata and any existing generated skills without writing files.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.check:
        differences = check_plugin_layout()
        if differences:
            for difference in differences:
                print(difference)
            return 1
        print("plugin sync check ok")
        return 0

    destination = sync_plugin_skills()
    print(destination.relative_to(PLUGIN_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
