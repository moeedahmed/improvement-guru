#!/usr/bin/env python3
"""Validate and build the draft Improvement Guru ChatGPT directory package."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path, PurePosixPath
import re
import sys
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "plugins/chatgpt/improvement-guru"
ROOT_FILES = {"plugin.json", "README.md", "PRIVACY.md", "TERMS.md", "SUPPORT.md"}
EXCLUDED = {"REVIEW_TESTS.md", "SUBMISSION_CHECKLIST.md", "__pycache__"}
CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
PLUGIN_NAME = re.compile(r"[a-z0-9]+(?:[-_][a-z0-9]+)*")
SKILL_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
NUMBER = r"(?:0|[1-9][0-9]*)"
PRERELEASE = rf"(?:{NUMBER}|[0-9]*[A-Za-z-][0-9A-Za-z-]*)"
SEMVER = re.compile(
    rf"{NUMBER}\.{NUMBER}\.{NUMBER}(?:-{PRERELEASE}(?:\.{PRERELEASE})*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
)
PUBLIC_TITLES = re.compile(r"\b(?:founder|CEO|entrepreneur)\b", re.IGNORECASE)
NHS_LIKE = re.compile(r"(?<!\d)\d{3}[ \t]*\d{3}[ \t]*\d{4}(?!\d)")
SKILL_LINK = re.compile(r"`+((?:references|assets)/[^`\r\n]+)`+")
LIMITS = re.compile(r"^## Limits[^\S\n]*\n(.*?)(?=^#{1,2}[ \t]|\Z)", re.MULTILINE | re.DOTALL)


def _included(path: Path) -> bool:
    if any(part.startswith(".") or part in EXCLUDED for part in path.parts):
        return False
    if len(path.parts) == 1:
        return path.name in ROOT_FILES
    return path.parts[0] in {"assets", "skills"}


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant {value}")


def _load_manifest(path: Path) -> dict:
    manifest = json.loads(path.read_text(encoding="utf-8"), parse_constant=_reject_json_constant)
    if not isinstance(manifest, dict):
        raise ValueError("expected a JSON object")
    return manifest


def _local_file(root: Path, value: object, *, dot_prefix: bool = False) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value or "\0" in value:
        return None
    if dot_prefix and not value.startswith("./"):
        return None
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    path = root.joinpath(*relative.parts)
    if path.is_file() and path.resolve().is_relative_to(root.resolve()):
        return path
    return None


def _validate_urls(value: object, location: str, errors: list[str]) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_urls(item, f"{location}[{index}]", errors)
    if not isinstance(value, dict):
        return
    for key, item in value.items():
        field = f"{location}.{key}"
        if key.lower().endswith("url"):
            try:
                valid = (
                    isinstance(item, str)
                    and len(item) <= 1024
                    and item.startswith("https://")
                    and not any(char.isspace() or ord(char) < 32 for char in item)
                    and bool(urlsplit(item).hostname)
                )
            except ValueError:
                valid = False
            if not valid:
                errors.append(f"{field} must be an HTTPS URL of at most 1024 characters")
        _validate_urls(item, field, errors)


def _luminance(colour: str) -> float:
    digits = colour[1:]
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    channels = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def _validate_icon(root: Path, field: str, value: object, errors: list[str]) -> None:
    path = _local_file(root, value, dot_prefix=True)
    if path is None or not _included(path.relative_to(root)) or path.suffix.lower() not in IMAGE_SUFFIXES:
        errors.append(f"interface.{field} must be an existing ./-relative packaged image")
        return
    if path.suffix.lower() != ".svg":
        return
    try:
        svg = ElementTree.parse(path).getroot()
        x, y, width, height = map(float, svg.attrib["viewBox"].replace(",", " ").split())
        valid = (
            svg.tag in {"svg", "{http://www.w3.org/2000/svg}svg"}
            and all(math.isfinite(value) for value in (x, y, width, height))
            and width == height >= 48
        )
    except (ElementTree.ParseError, LookupError, ValueError):
        valid = False
    if not valid:
        errors.append(f"interface.{field} SVG must have a square viewBox of at least 48")


def _validate_interface(root: Path, interface: dict, errors: list[str]) -> None:
    for field, limit in {
        "displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80,
    }.items():
        value = interface.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"interface.{field} must be non-empty and at most {limit} characters")
        elif field in {"displayName", "shortDescription"} and value.splitlines() != [value]:
            errors.append(f"interface.{field} must be one line")

    if "not clinical advice" not in str(interface.get("longDescription", "")):
        errors.append('interface.longDescription must contain "not clinical advice"')

    category = interface.get("category")
    if not isinstance(category, str) or category not in CATEGORIES:
        errors.append("interface.category must be an allowed directory category")

    for field, count, limit in (("capabilities", 20, 120), ("defaultPrompt", 3, 128)):
        items = interface.get(field, [])
        if (
            not isinstance(items, list) or len(items) > count
            or any(not isinstance(item, str) or len(item) > limit for item in items)
        ):
            errors.append(f"interface.{field} must have at most {count} text items of at most {limit} characters")
        elif field == "defaultPrompt" and len(set(items)) != len(items):
            errors.append("interface.defaultPrompt items must be unique")

    for field, background in (("brandColor", "#FFFFFF"), ("brandColorDark", "#212121")):
        colour = interface.get(field)
        if not isinstance(colour, str) or not re.fullmatch(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})", colour):
            errors.append(f"interface.{field} must be a hex colour")
            continue
        darker, lighter = sorted((_luminance(colour), _luminance(background)))
        if (lighter + 0.05) / (darker + 0.05) < 2:
            errors.append(f"interface.{field} must have at least 2:1 contrast against {background}")

    for field in ("logo", "composerIcon"):
        _validate_icon(root, field, interface.get(field), errors)


def _validate_manifest(root: Path, manifest: dict, errors: list[str]) -> str:
    name = manifest.get("name")
    if not isinstance(name, str) or len(name) > 64 or not PLUGIN_NAME.fullmatch(name):
        errors.append("plugin.json name must be kebab-case ASCII and at most 64 characters")
        name = ""
    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append("plugin.json version must be SemVer")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("plugin.json description must be non-empty")
    for key in sorted({"apps", "mcpServers", "review"} & manifest.keys()):
        errors.append(f"plugin.json must not contain the top-level {key} key")

    _validate_urls(manifest, "plugin.json", errors)
    extensions = manifest.get("extensions")
    openai = extensions.get("com.openai") if isinstance(extensions, dict) else None
    if not isinstance(openai, dict):
        errors.append("plugin.json must contain an extensions.com.openai object")
        return name
    interface = openai.get("interface")
    if isinstance(interface, dict):
        _validate_interface(root, interface, errors)
    else:
        errors.append("plugin.json must contain an extensions.com.openai.interface object")
    onboarding = _local_file(root, openai.get("onboardingSkill"))
    if onboarding is None or not _included(onboarding.relative_to(root)):
        errors.append("onboardingSkill must point to an existing packaged file")
    return name


def _skill_metadata(content: str) -> dict[str, str]:
    """Read the simple scalar fields used in this package's skill frontmatter."""
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    fields: dict[str, str] = {}
    key = ""
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0].isspace() and key:
            fields[key] += " " + line.strip()
            continue
        key, separator, value = line.partition(":")
        key = key.strip()
        if key not in {"name", "description"}:
            key = ""
            continue
        if not separator or key in fields:
            return {}
        value = value.strip()
        if re.fullmatch(r"[|>][+-]?", value):
            value = ""
        elif value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                return {}
        elif value.startswith("'"):
            if len(value) < 2 or not value.endswith("'"):
                return {}
            value = value[1:-1].replace("''", "'")
        elif value.startswith(("[", "{")) or value in {"~", "null", "true", "false"}:
            return {}
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0]
        fields[key] = value
    return {key: value.strip() for key, value in fields.items()}


def _validate_skills(root: Path, paths: list[Path], plugin_name: str, errors: list[str]) -> None:
    skills = root / "skills"
    names: set[str] = set()
    if skills.is_symlink() or not skills.is_dir():
        errors.append("skills/ directory is required")
        return
    for directory in sorted(skills.iterdir()):
        if not directory.is_dir():
            errors.append(f"skills/{directory.name} is a loose file")
            continue
        if directory.name.startswith(".") or directory.name in EXCLUDED:
            continue
        path = directory / "SKILL.md"
        label = path.relative_to(root).as_posix()
        if path not in paths:
            errors.append(f"{label} is required")
            continue
        content = path.read_text(encoding="utf-8")
        metadata = _skill_metadata(content)
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if not SKILL_NAME.fullmatch(name):
            errors.append(f"{label} frontmatter name must be kebab-case")
        elif name in names:
            errors.append(f"{label} has a duplicate skill name")
        names.add(name)
        if len(f"{plugin_name}:{name}") > 64:
            errors.append(f"{label} plugin:skill name must be at most 64 characters")
        if not description or len(description) > 1024:
            errors.append(f"{label} frontmatter description must be non-empty and at most 1024 characters")

        for anchor in ("No patient or identifiable details", "When to stop or decline"):
            if anchor not in content:
                errors.append(f'{label} must contain "{anchor}"')

        for link in sorted(set(SKILL_LINK.findall(content))):
            target = _local_file(directory, link)
            if target not in paths:
                errors.append(f"{label} references a missing packaged file: {link}")

    skill = skills / "qi-project-starter"
    sections = []
    for relative in ("assets/starter-pack-template.md", "references/worked-example.md"):
        path = skill / relative
        if path not in paths:
            errors.append(f"{path.relative_to(root).as_posix()} is required for the Limits check")
            continue
        match = LIMITS.search(path.read_text(encoding="utf-8"))
        if match is None or not match[1].strip():
            errors.append(f"{path.relative_to(root).as_posix()} must contain a non-empty ## Limits section")
        else:
            sections.append(match[1].strip("\n"))
    if len(sections) == 2 and sections[0] != sections[1]:
        errors.append("The ## Limits sections in starter-pack-template.md and worked-example.md must match")


def _validate_text(path: Path, relative: Path, manifest: dict | None, errors: list[str]) -> None:
    # Package text is UTF-8. Other file types may be binary assets.
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        if path.suffix.lower() in {".json", ".md", ".svg", ".txt"}:
            errors.append(f"{relative.as_posix()} must be UTF-8 text")
        return
    if relative == Path("plugin.json") and manifest is not None:
        # Check decoded JSON too, so Unicode escapes cannot hide a forbidden character.
        content += "\n" + json.dumps(manifest, ensure_ascii=False)
    label = relative.as_posix()
    if "\u2014" in content:
        errors.append(f"{label} contains an em dash (U+2014)")
    if label in ROOT_FILES or relative.parts[0] == "skills":
        if PUBLIC_TITLES.search(content):
            errors.append(f"{label} contains a prohibited job title")
        if any(not re.sub(r"[ \t]", "", match[0]).startswith("999") for match in NHS_LIKE.finditer(content)):
            errors.append(f"{label} contains an NHS-number-like sequence outside the synthetic 999 range")


def _inspect_package(root: Path, errors: list[str]) -> tuple[dict, list[Path]]:
    if not root.is_dir():
        errors.append("Package directory does not exist")
        return {}, []
    manifest = None
    plugin_name = ""
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.name in {".app.json", ".mcp.json"} or (path.name == "hooks" and path.is_dir()):
            errors.append(f"{relative.as_posix()} is prohibited in a skills-only package")
        if path.is_symlink():
            errors.append(f"{relative.as_posix()} must not be a symbolic link")
        elif path.is_file():
            files.append(path)

    packaged = sorted(
        (path for path in files if _included(path.relative_to(root))),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for name in sorted(ROOT_FILES):
        if root / name not in packaged:
            errors.append(f"{name} is required")
    if root / "plugin.json" in packaged:
        try:
            manifest = _load_manifest(root / "plugin.json")
        except (ValueError, RecursionError) as exc:
            errors.append(f"plugin.json is invalid: {exc}")
        else:
            plugin_name = _validate_manifest(root, manifest, errors)

    for path in files:
        relative = path.relative_to(root)
        if "__pycache__" not in relative.parts:
            _validate_text(path, relative, manifest, errors)
    _validate_skills(root, packaged, plugin_name, errors)
    return manifest or {}, packaged


def _check_package(root: Path) -> tuple[dict, list[Path], list[str]]:
    errors: list[str] = []
    try:
        manifest, files = _inspect_package(root, errors)
    except (OSError, UnicodeError, RecursionError) as exc:
        errors.append(f"Unable to read package: {exc}")
        return {}, [], errors
    return manifest, files, errors


def validate_package(root: Path) -> list[str]:
    """Return validation errors for a local ChatGPT directory package."""
    return _check_package(root)[2]


def build_zip(root: Path, out_dir: Path) -> Path:
    """Build a deterministic submission ZIP or raise ValueError if invalid."""
    manifest, files, errors = _check_package(root)
    if errors:
        raise ValueError("\n".join(errors))
    name = manifest["name"]
    destination = out_dir / f"{name}-{manifest['version']}.zip"
    out_dir.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=out_dir, delete=False) as scratch:
        temporary = Path(scratch.name)
    try:
        with ZipFile(temporary, "w") as archive:
            for path in files:
                entry = ZipInfo(f"{name}/{path.relative_to(root).as_posix()}", (1980, 1, 1, 0, 0, 0))
                entry.create_system = 3
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, path.read_bytes(), compress_type=ZIP_DEFLATED)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "dist", help="ZIP output directory")
    parser.add_argument("--check-only", action="store_true", help="validate without writing a ZIP")
    args = parser.parse_args(argv)
    if args.check_only:
        errors = validate_package(PACKAGE_ROOT)
        if not errors:
            print("Package validation passed.")
            return 0
        for error in errors:
            print(f"Error: {error}", file=sys.stderr)
        return 1
    try:
        destination = build_zip(PACKAGE_ROOT, args.out)
        with ZipFile(destination) as archive:
            count = len(archive.infolist())
    except (OSError, ValueError) as exc:
        for error in str(exc).splitlines():
            print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"{destination} ({count} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
