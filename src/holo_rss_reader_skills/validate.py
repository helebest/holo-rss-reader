"""Repository validation for canonical Holo RSS Reader skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
PLUGIN_NAME = "holo-rss-reader"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_NAME
PLUGIN_SKILLS_DIR = PLUGIN_ROOT / "skills"
CODEX_PLUGIN_MANIFEST = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
CLAUDE_PLUGIN_MANIFEST = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
OPENCLAW_PLUGIN_MANIFEST = PLUGIN_ROOT / "openclaw.plugin.json"
OPENCLAW_PACKAGE_JSON = PLUGIN_ROOT / "package.json"
MARKETPLACE_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
SKILL_NAMES = ["holo-rss-reader"]
BANNED_NAMES = {
    ".env",
    ".venv",
    "CHANGELOG.md",
    "README.md",
    "dist",
    "pyproject.toml",
    "uv.lock",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationError(Exception):
    """Raised when repository validation fails."""


def load_json(path: Path) -> dict:
    if not path.exists():
        raise ValidationError(f"Missing {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def project_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    if match is None:
        raise ValidationError("pyproject.toml is missing project version")
    return match.group(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValidationError(f"{path} is missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValidationError(f"{path} has unterminated YAML frontmatter")

    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValidationError(f"{path} has invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def validate_skill(skill_dir: Path) -> None:
    name = skill_dir.name
    if not NAME_RE.match(name):
        raise ValidationError(f"Invalid skill directory name: {name}")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValidationError(f"Missing {skill_md}")

    frontmatter = parse_frontmatter(skill_md)
    if set(frontmatter) != {"name", "description"}:
        raise ValidationError(f"{skill_md} frontmatter must contain only name and description")
    if frontmatter.get("name") != name:
        raise ValidationError(f"{skill_md} name must match directory name")
    if not frontmatter.get("description"):
        raise ValidationError(f"{skill_md} description is required")

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and not (scripts_dir / "requirements.txt").exists():
        raise ValidationError(f"{scripts_dir} must contain requirements.txt")

    for path in skill_dir.rglob("*"):
        if path.name in BANNED_NAMES:
            raise ValidationError(f"Banned file or directory in skill package: {path}")


def validate_plugin_manifests() -> None:
    legacy_paths = [
        ROOT / "SKILL.md",
        ROOT / "scripts",
        ROOT / "references",
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / "openclaw.plugin.json",
        ROOT / "openclaw_deploy_skill.sh",
    ]
    for path in legacy_paths:
        if path.exists():
            raise ValidationError(f"{path} is a legacy root skill/plugin path; use {SKILLS_DIR}")

    version = project_version()
    expected = {
        CLAUDE_PLUGIN_MANIFEST: "./skills/",
        CODEX_PLUGIN_MANIFEST: "./skills/",
        OPENCLAW_PLUGIN_MANIFEST: ["./skills"],
    }
    for manifest, expected_skills in expected.items():
        data = load_json(manifest)
        if data.get("name") != PLUGIN_NAME:
            raise ValidationError(f"{manifest} name must be {PLUGIN_NAME}")
        if data.get("version") != version:
            raise ValidationError(f"{manifest} version must match pyproject.toml")
        if data.get("skills") != expected_skills:
            raise ValidationError(f"{manifest} skills must be {expected_skills!r}")

    package_json = load_json(OPENCLAW_PACKAGE_JSON)
    if package_json.get("name") != PLUGIN_NAME:
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} name must be {PLUGIN_NAME}")
    if package_json.get("version") != version:
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} version must match pyproject.toml")
    if package_json.get("type") != "module":
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} type must be module")
    if package_json.get("private") is not False:
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} private must be false")
    if package_json.get("files") != ["openclaw.plugin.json", "skills"]:
        raise ValidationError(
            f"{OPENCLAW_PACKAGE_JSON} files must include only openclaw.plugin.json and skills"
        )

    openclaw = package_json.get("openclaw")
    if not isinstance(openclaw, dict):
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} must contain openclaw metadata")
    compat = openclaw.get("compat")
    build = openclaw.get("build")
    if not isinstance(compat, dict) or not compat.get("pluginApi"):
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} missing openclaw.compat.pluginApi")
    if not isinstance(build, dict) or not build.get("openclawVersion"):
        raise ValidationError(f"{OPENCLAW_PACKAGE_JSON} missing openclaw.build.openclawVersion")


def validate_marketplace() -> None:
    payload = load_json(MARKETPLACE_PATH)
    plugins = payload.get("plugins")
    if not isinstance(plugins, list):
        raise ValidationError(f"{MARKETPLACE_PATH} plugins must be an array")

    matches = [
        entry for entry in plugins if isinstance(entry, dict) and entry.get("name") == PLUGIN_NAME
    ]
    if len(matches) != 1:
        raise ValidationError(f"{MARKETPLACE_PATH} must contain exactly one {PLUGIN_NAME} entry")

    entry = matches[0]
    if entry.get("source") != {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"}:
        raise ValidationError(f"{MARKETPLACE_PATH} has invalid source for {PLUGIN_NAME}")
    if entry.get("policy") != {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }:
        raise ValidationError(f"{MARKETPLACE_PATH} has invalid policy for {PLUGIN_NAME}")
    if entry.get("category") != "Productivity":
        raise ValidationError(f"{MARKETPLACE_PATH} category must be Productivity")


def validate_generated_plugin_skills() -> None:
    if not PLUGIN_SKILLS_DIR.exists():
        return

    actual = sorted(path.name for path in PLUGIN_SKILLS_DIR.iterdir() if path.is_dir())
    if actual != sorted(SKILL_NAMES):
        raise ValidationError(f"Unexpected generated plugin skills: {actual}")
    for skill_name in SKILL_NAMES:
        validate_skill(PLUGIN_SKILLS_DIR / skill_name)


def validate_all() -> None:
    if not SKILLS_DIR.exists():
        raise ValidationError("Missing skills directory")

    actual = sorted(path.name for path in SKILLS_DIR.iterdir() if path.is_dir())
    if actual != sorted(SKILL_NAMES):
        raise ValidationError(f"Unexpected skills: {actual}")

    for skill_name in SKILL_NAMES:
        validate_skill(SKILLS_DIR / skill_name)

    validate_plugin_manifests()
    validate_marketplace()
    validate_generated_plugin_skills()


def main() -> int:
    try:
        validate_all()
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print("validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
