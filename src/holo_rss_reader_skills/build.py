"""Build disposable distribution artifacts from the canonical skills directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from .validate import (
    CLAUDE_PLUGIN_MANIFEST,
    CODEX_PLUGIN_MANIFEST,
    OPENCLAW_EXTENSION_ENTRY,
    OPENCLAW_PLUGIN_MANIFEST,
    OPENCLAW_PACKAGE_JSON,
    PLUGIN_ROOT,
    ROOT,
    SKILL_NAMES,
    SKILLS_DIR,
    parse_frontmatter,
    validate_all,
)

DIST_DIR = ROOT / "dist"
EXCLUDE_NAMES = {
    ".env",
    ".pytest_cache",
    ".venv",
    "__pycache__",
}
EXCLUDE_SUFFIXES = {".pyc", ".pyo"}


def should_exclude(path: Path) -> bool:
    return path.name in EXCLUDE_NAMES or path.suffix in EXCLUDE_SUFFIXES


def iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(should_exclude(Path(part)) for part in relative.parts):
            continue
        if should_exclude(path):
            continue
        if path.is_file():
            yield path


def zip_tree(source: Path, output: Path, arc_prefix: str | None = None) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in iter_files(source):
            relative = file_path.relative_to(source)
            arcname = Path(arc_prefix) / relative if arc_prefix else relative
            archive.write(file_path, arcname.as_posix())


def add_tree_to_zip(archive: zipfile.ZipFile, source: Path, destination: Path) -> None:
    for file_path in iter_files(source):
        relative = file_path.relative_to(source)
        archive.write(file_path, (destination / relative).as_posix())


def build_skill_zips() -> list[Path]:
    outputs = []
    for skill_name in SKILL_NAMES:
        skill_dir = SKILLS_DIR / skill_name
        output = DIST_DIR / "skills" / f"{skill_name}.zip"
        zip_tree(skill_dir, output, arc_prefix=skill_name)
        outputs.append(output)
    return outputs


def build_plugin_zip(name: str, manifest: Path, extra_files: list[Path] | None = None) -> Path:
    output = DIST_DIR / "plugins" / f"{name}.zip"
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(manifest, manifest.relative_to(PLUGIN_ROOT).as_posix())
        for extra_file in extra_files or []:
            archive.write(extra_file, extra_file.relative_to(PLUGIN_ROOT).as_posix())
        add_tree_to_zip(archive, SKILLS_DIR, Path("skills"))
    return output


def artifact_url(base_url: str, skill_name: str) -> str:
    if base_url:
        return f"{base_url.rstrip('/')}/skills/{skill_name}.zip"
    return f"../../skills/{skill_name}.zip"


def build_well_known(base_url: str) -> list[Path]:
    skills = []
    for skill_name in SKILL_NAMES:
        metadata = parse_frontmatter(SKILLS_DIR / skill_name / "SKILL.md")
        skills.append(
            {
                "name": skill_name,
                "description": metadata["description"],
                "type": "archive",
                "url": artifact_url(base_url, skill_name),
            }
        )

    outputs = []
    for relative in [
        Path("site/.well-known/skills/index.json"),
        Path("site/.well-known/agent-skills/index.json"),
    ]:
        output = DIST_DIR / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "$schema": "https://schemas.agentskills.io/discovery/0.2.0/schema.json",
            "publisher": {"name": "holo"},
            "skills": skills,
        }
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        outputs.append(output)
    return outputs


def write_checksums(paths: list[Path]) -> Path:
    output = DIST_DIR / "checksums.txt"
    lines = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(DIST_DIR).as_posix()}")
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def build(base_url: str = "", clean: bool = True) -> list[Path]:
    validate_all()
    if clean and DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)

    artifacts: list[Path] = []
    artifacts.extend(build_skill_zips())
    artifacts.append(build_plugin_zip("claude-holo-rss-reader-plugin", CLAUDE_PLUGIN_MANIFEST))
    artifacts.append(build_plugin_zip("codex-holo-rss-reader-plugin", CODEX_PLUGIN_MANIFEST))
    artifacts.append(
        build_plugin_zip(
            "openclaw-holo-rss-reader-plugin",
            OPENCLAW_PLUGIN_MANIFEST,
            extra_files=[OPENCLAW_PACKAGE_JSON, OPENCLAW_EXTENSION_ENTRY],
        )
    )
    artifacts.extend(build_well_known(base_url))
    artifacts.append(write_checksums([path for path in artifacts if path.is_file()]))
    return artifacts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Holo RSS Reader skill release artifacts.")
    parser.add_argument(
        "--base-url", default="", help="Base URL used in well-known discovery indexes."
    )
    parser.add_argument(
        "--no-clean", action="store_true", help="Do not remove dist/ before building."
    )
    args = parser.parse_args()

    artifacts = build(base_url=args.base_url, clean=not args.no_clean)
    for artifact in artifacts:
        print(artifact.relative_to(ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
