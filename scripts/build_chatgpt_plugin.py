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
from unicodedata import normalize
from urllib.parse import urlsplit
from xml.etree import ElementTree
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = REPO_ROOT / "plugins/chatgpt/improvement-guru"
PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PROHIBITED_FIELDS = {"mcp", "mcpServers", "apps", "hooks", "review"}
ROOT_FILES = {"plugin.json", "README.md", "PRIVACY.md", "TERMS.md", "SUPPORT.md"}
EXCLUDED = {"REVIEW_TESTS.md", "SUBMISSION_CHECKLIST.md", "__pycache__"}
CATEGORIES = {
    "Productivity", "Creativity", "Developer Tools", "Business & Operations",
    "Data & Analytics", "Communication", "Education & Research", "Security",
    "Finance", "Healthcare", "Travel", "Entertainment", "Other",
}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
# OpenAI submission errors and listing metadata document these limits.
MAX_IMAGE_BYTES = 5 * 1024**2
MAX_ARCHIVE_BYTES = 100_000_000
MAX_MEMBER_BYTES = 100 * 1024**2
MAX_EXTRACTED_BYTES = 512 * 1024**2
MAX_ARCHIVE_ENTRIES = 5_000
MAX_MEMBER_SEGMENTS = 20
SVG_NUMBER = re.compile(r"[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")
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
YAML_PLAIN_NUMBER = re.compile(
    r"[+-]?(?:0b[01_]+|0o[0-7_]+|0x[0-9a-f_]+|"
    r"(?:[0-9][0-9_]*(?:\.[0-9_]*)?|\.[0-9_]+)(?:e[+-]?[0-9]+)?|"
    r"[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?|\.inf|\.nan)",
    re.IGNORECASE,
)
YAML_PLAIN_TIMESTAMP = re.compile(
    r"[0-9]{4}-(?:[0-9]{2}-[0-9]{2}|"
    r"[0-9]{1,2}-[0-9]{1,2}[Tt \t]+[0-9]{1,2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]*)?(?:[ \t]*(?:Z|[+-][0-9]{1,2}(?::[0-9]{2})?))?)"
)


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


def _valid_url(value: object, limit: int | None) -> bool:
    if (
        not isinstance(value, str) or (limit is not None and len(value) > limit)
        or not value.startswith("https://") or "\\" in value
        or any(char.isspace() or ord(char) < 32 or ord(char) == 127 for char in value)
    ):
        return False
    try:
        url = urlsplit(value)
        _ = url.port  # urlsplit defers port validation until this attribute is read.
        return bool(url.hostname) and url.username is None
    except ValueError:
        return False


def _validate_manifest_fields(value: object, location: str, errors: list[str]) -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_manifest_fields(item, f"{location}[{index}]", errors)
    if not isinstance(value, dict):
        return
    for key, item in value.items():
        field = f"{location}.{key}"
        if key in PROHIBITED_FIELDS:
            errors.append(f"{field} is prohibited in a skills-only package")
        repository_url = field == "plugin.json.repository" and isinstance(item, str)
        if key.lower().endswith("url") or field == "plugin.json.homepage" or repository_url:
            limit = 2048 if field in {"plugin.json.homepage", "plugin.json.author.url"} else 1024
            if repository_url:
                limit = None
            if not _valid_url(item, limit):
                length = f" of at most {limit} characters" if limit is not None else ""
                errors.append(f"{field} must be an HTTPS URL{length} with a host and no credentials")
        _validate_manifest_fields(item, field, errors)


def _luminance(colour: str) -> float:
    digits = colour[1:]
    channels = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return sum(weight * channel for weight, channel in zip((0.2126, 0.7152, 0.0722), linear))


def _svg_dimensions(data: bytes) -> tuple[float, float] | None:
    try:
        svg = ElementTree.fromstring(data)
    except (ElementTree.ParseError, LookupError, ValueError):
        return None
    if svg.tag not in {"svg", "{http://www.w3.org/2000/svg}svg"}:
        return None
    if "viewBox" in svg.attrib:
        values = re.split(r"\s*,\s*|\s+", svg.attrib["viewBox"].strip())
        if len(values) != 4:
            return None
    else:
        values = [svg.get(field, "").strip() for field in ("width", "height")]
    if not all(SVG_NUMBER.fullmatch(value) and math.isfinite(float(value)) for value in values):
        return None
    return float(values[-2]), float(values[-1])


def _validate_icon(root: Path, field: str, value: object, errors: list[str]) -> None:
    path = _local_file(root, value, dot_prefix=True)
    if path is None or not _included(path.relative_to(root)) or path.suffix.lower() not in IMAGE_SUFFIXES:
        errors.append(f"interface.{field} must be an existing ./-relative packaged image")
        return
    if path.suffix.lower() != ".svg":
        errors.append(
            f"interface.{field}: raster icons are not checked by this script "
            "(it cannot fully decode them without extra libraries); use a square SVG, "
            "or check the raster image by hand before upload"
        )
        return
    with path.open("rb") as image:
        data = image.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        errors.append(f"interface.{field} image must not exceed 5 MiB")
        return
    dimensions = _svg_dimensions(data)
    if dimensions is None:
        errors.append(f"interface.{field} SVG must have a numeric viewBox or width and height")
        return
    width, height = dimensions
    if not width == height >= 48:
        errors.append(f"interface.{field} image must be square and at least 48×48")


def _validate_interface(root: Path, interface: dict, errors: list[str]) -> None:
    for field, limit in {
        "displayName": 30, "shortDescription": 30, "longDescription": 4000, "developerName": 80,
    }.items():
        value = interface.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            errors.append(f"interface.{field} must be non-empty and at most {limit} characters")
        elif field != "longDescription" and value.splitlines() != [value]:
            errors.append(f"interface.{field} must be one line")

    if "not clinical advice" not in str(interface.get("longDescription", "")):
        errors.append('interface.longDescription must contain "not clinical advice"')

    category = interface.get("category")
    if not isinstance(category, str) or category not in CATEGORIES:
        errors.append("interface.category must be an allowed directory category")

    for field, count, limit in (("capabilities", 20, 120), ("defaultPrompt", 3, 128)):
        items = interface.get(field, [])
        if field == "defaultPrompt" and isinstance(items, str):
            items = [items]
        if (
            not isinstance(items, list) or len(items) > count
            or any(not isinstance(item, str) or not item.strip() or len(item) > limit for item in items)
        ):
            errors.append(f"interface.{field} allows up to {count} non-blank text items of at most {limit} characters")
        elif any(item.splitlines() != [item] for item in items):
            errors.append(f"interface.{field} items must be one line")
        elif field == "defaultPrompt":
            prompts = {normalize("NFC", " ".join(item.split())) for item in items}
            if len(prompts) != len(items):
                errors.append("interface.defaultPrompt items must be unique after normalising whitespace and Unicode")

    for field, background in (("brandColor", "#FFFFFF"), ("brandColorDark", "#212121")):
        colour = interface.get(field)
        if not isinstance(colour, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", colour):
            errors.append(f"interface.{field} must be a six-digit #RRGGBB colour")
            continue
        darker, lighter = sorted((_luminance(colour), _luminance(background)))
        if (lighter + 0.05) / (darker + 0.05) < 2:
            errors.append(f"interface.{field} must have at least 2:1 contrast against {background}")

    for field in ("logo", "composerIcon"):
        _validate_icon(root, field, interface.get(field), errors)
    for field in ("logoDark", "composerIconDark"):
        if field in interface:
            _validate_icon(root, field, interface[field], errors)


def _validate_manifest(root: Path, manifest: dict, errors: list[str]) -> str:
    if manifest.get("$schema") != PLUGIN_SCHEMA:
        errors.append(f"plugin.json $schema must equal {PLUGIN_SCHEMA}")
    name = manifest.get("name")
    if not isinstance(name, str) or len(name) > 64 or not PLUGIN_NAME.fullmatch(name):
        errors.append("plugin.json name must be kebab-case ASCII and at most 64 characters")
        name = ""
    version = manifest.get("version")
    if not isinstance(version, str) or len(version) > 64 or not SEMVER.fullmatch(version):
        errors.append("plugin.json version must be SemVer and at most 64 characters")
    description = manifest.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append("plugin.json description must be non-empty")
    _validate_manifest_fields(manifest, "plugin.json", errors)
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
    relative = onboarding.relative_to(root) if onboarding is not None else None
    if (
        relative is None or not _included(relative) or len(relative.parts) != 3
        or relative.parts[0] != "skills" or relative.name != "SKILL.md"
    ):
        errors.append("onboardingSkill must point to an existing packaged skills/<name>/SKILL.md")
    return name


def _skill_metadata(content: str) -> dict[str, str]:
    """Read a flat frontmatter mapping of single-line text values."""
    lines = content.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("frontmatter must start with ---")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("frontmatter must end with ---") from exc
    fields: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_-]*):[ \t]+(.+)", line)
        if match is None:
            raise ValueError(f"frontmatter line {number} must be a key: value pair")
        key, value = match.groups()
        if key in fields:
            raise ValueError(f"frontmatter line {number} repeats key {key}")
        value = value.strip()
        if value.startswith('"'):
            try:
                value, end_quote = json.JSONDecoder().raw_decode(value)
            except ValueError as exc:
                raise ValueError(f"frontmatter line {number} has an invalid quoted value") from exc
            if not re.fullmatch(r"(?:[ \t]+#.*)?", match[2].strip()[end_quote:]):
                raise ValueError(f"frontmatter line {number} has text after the quoted value")
        elif value.startswith("'"):
            quoted = re.fullmatch(r"'((?:[^']|'')*)'(?:[ \t]+#.*)?", value)
            if quoted is None:
                raise ValueError(f"frontmatter line {number} has an invalid quoted value")
            value = quoted[1].replace("''", "'")
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0]
            lower = value.lower()
            if (
                not value or value[0] in "[]{}|>&*!#%@`,"
                or re.search(r"(^[-?:](\s|$)|:(\s|$))", value)
                or lower in {"~", "null", "true", "false"}
                or (key in {"name", "description"} and (
                    lower in {"y", "n", "yes", "no", "on", "off"}
                    or YAML_PLAIN_NUMBER.fullmatch(value)
                    or YAML_PLAIN_TIMESTAMP.fullmatch(value)
                ))
            ):
                raise ValueError(f"frontmatter line {number} must contain a single-line text value")
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
        try:
            metadata = _skill_metadata(content)
        except ValueError as exc:
            errors.append(f"{label} {exc}")
            continue
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


def _validate_archive_members(root: Path, files: list[Path], errors: list[str]) -> None:
    if len(files) > MAX_ARCHIVE_ENTRIES:
        errors.append("ZIP must contain at most 5,000 entries")
    seen: dict[str, str] = {}
    total = 0
    for path in files:
        relative = path.relative_to(root)
        name = relative.as_posix()
        if "\\" in name:
            errors.append(f"{name} contains a backslash")
        # The archive adds the plugin name as its enclosing directory.
        if len(relative.parts) + 1 > MAX_MEMBER_SEGMENTS:
            errors.append(f"{name} would exceed 20 ZIP path segments")
        canonical = normalize("NFC", normalize("NFC", name).casefold())
        if canonical in seen:
            errors.append(f"{name} collides with {seen[canonical]} after case and Unicode normalisation")
        seen[canonical] = name
        size = path.stat().st_size
        if size > MAX_MEMBER_BYTES:
            errors.append(f"{name} exceeds the 100 MiB ZIP member limit")
        total += size
    if total > MAX_EXTRACTED_BYTES:
        errors.append("Extracted ZIP must not exceed 512 MiB")


def _inspect_package(root: Path, errors: list[str]) -> tuple[dict, list[Path]]:
    if not root.is_dir():
        errors.append("Package directory does not exist")
        return {}, []
    manifest = None
    plugin_name = ""
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if path.name in {".app.json", ".mcp.json"} or relative == Path("mcp.json") or (
            path.name == "hooks" and path.is_dir()
        ):
            errors.append(f"{relative.as_posix()} is prohibited in a skills-only package")
        if path.is_symlink():
            errors.append(f"{relative.as_posix()} must not be a symbolic link")
        elif path.is_file():
            files.append(path)

    packaged = sorted(
        (path for path in files if _included(path.relative_to(root))),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    earlier_errors = len(errors)
    _validate_archive_members(root, packaged, errors)
    if len(errors) != earlier_errors:
        return {}, packaged
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
    if out_dir.resolve().is_relative_to(root.resolve()):
        raise ValueError("ZIP output directory must be outside the package root")
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
        if temporary.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("Compressed ZIP must not exceed 100 MB")
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
