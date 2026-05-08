from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

from holo_rss_reader_skills.build import build
from holo_rss_reader_skills.sync_plugin import compare_skill_trees, sync_plugin_skills
from holo_rss_reader_skills.validate import (
    CLAUDE_PLUGIN_MANIFEST,
    CODEX_PLUGIN_MANIFEST,
    MARKETPLACE_PATH,
    OPENCLAW_PLUGIN_MANIFEST,
    PLUGIN_NAME,
    PLUGIN_SKILLS_DIR,
    ROOT,
    SKILL_NAMES,
    SKILLS_DIR,
    validate_all,
)


def project_version() -> str:
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    assert match is not None
    return match.group(1)


def test_skills_validate() -> None:
    validate_all()


def test_skill_script_shows_help() -> None:
    script = ROOT / "skills/holo-rss-reader/scripts/main.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_skill_script_requirements_are_runtime_only() -> None:
    requirements = ROOT / "skills/holo-rss-reader/scripts/requirements.txt"
    text = requirements.read_text(encoding="utf-8")
    normalized = text.lower()

    for package in ["feedparser", "requests", "defusedxml", "beautifulsoup4", "lxml"]:
        assert package in normalized

    for package in ["pytest", "pytest-cov", "responses", "ruff"]:
        assert package not in normalized


def test_plugin_manifest_versions_match_project_version() -> None:
    version = project_version()
    manifests = [
        CLAUDE_PLUGIN_MANIFEST,
        CODEX_PLUGIN_MANIFEST,
        OPENCLAW_PLUGIN_MANIFEST,
    ]

    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["name"] == PLUGIN_NAME
        assert data["version"] == version


def test_plugin_wrapper_and_codex_marketplace_are_valid() -> None:
    assert not (ROOT / ".claude-plugin/plugin.json").exists()
    assert not (ROOT / ".codex-plugin/plugin.json").exists()
    assert not (ROOT / "openclaw.plugin.json").exists()

    codex = json.loads(CODEX_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    claude = json.loads(CLAUDE_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    openclaw = json.loads(OPENCLAW_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    assert codex["skills"] == "./skills/"
    assert claude["skills"] == "./skills/"
    assert openclaw["skills"] == ["./skills"]

    assert marketplace["plugins"] == [
        {
            "name": PLUGIN_NAME,
            "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }
    ]


def test_generated_plugin_skills_are_ignored_and_syncable(tmp_path: Path) -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert f"plugins/{PLUGIN_NAME}/skills/" in gitignore

    result = subprocess.run(
        ["git", "ls-files", "--", str(PLUGIN_SKILLS_DIR.relative_to(ROOT))],
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    assert result.stdout == ""

    generated = sync_plugin_skills(tmp_path / "skills")
    assert compare_skill_trees(SKILLS_DIR, generated) == []
    assert generated.joinpath("holo-rss-reader/SKILL.md").exists()


def test_build_outputs_are_generated_from_canonical_skills() -> None:
    artifacts = build(clean=True)
    artifact_names = {path.relative_to(ROOT / "dist").as_posix() for path in artifacts}
    checksum_entries = (ROOT / "dist/checksums.txt").read_text(encoding="utf-8").splitlines()
    checksummed_artifacts = [
        path for path in artifacts if path.is_file() and path.name != "checksums.txt"
    ]

    for skill_name in SKILL_NAMES:
        assert f"skills/{skill_name}.zip" in artifact_names
        with zipfile.ZipFile(ROOT / "dist" / "skills" / f"{skill_name}.zip") as archive:
            names = archive.namelist()
        assert f"{skill_name}/SKILL.md" in names
        assert not any("/pyproject.toml" in name for name in names)

    plugin_artifacts = {
        "plugins/claude-holo-rss-reader-plugin.zip": ".claude-plugin/plugin.json",
        "plugins/codex-holo-rss-reader-plugin.zip": ".codex-plugin/plugin.json",
        "plugins/openclaw-holo-rss-reader-plugin.zip": "openclaw.plugin.json",
    }
    for artifact_name, manifest_path in plugin_artifacts.items():
        assert artifact_name in artifact_names
        with zipfile.ZipFile(ROOT / "dist" / artifact_name) as archive:
            names = archive.namelist()
        assert manifest_path in names
        for skill_name in SKILL_NAMES:
            assert f"skills/{skill_name}/SKILL.md" in names
        assert not any(name.startswith("src/") for name in names)
        assert not any(name.startswith("tests/") for name in names)
        assert not any(name.startswith(".agents/") for name in names)
        assert not any(name.startswith("plugins/") for name in names)
        assert "pyproject.toml" not in names

    assert "site/.well-known/skills/index.json" in artifact_names
    assert "site/.well-known/agent-skills/index.json" in artifact_names
    for relative in [
        "site/.well-known/skills/index.json",
        "site/.well-known/agent-skills/index.json",
    ]:
        payload = json.loads((ROOT / "dist" / relative).read_text(encoding="utf-8"))
        assert [skill["name"] for skill in payload["skills"]] == SKILL_NAMES

    assert (ROOT / "dist/checksums.txt").exists()
    assert len(checksum_entries) == len(checksummed_artifacts)
    for artifact in checksummed_artifacts:
        assert artifact.relative_to(ROOT / "dist").as_posix() in "\n".join(checksum_entries)
