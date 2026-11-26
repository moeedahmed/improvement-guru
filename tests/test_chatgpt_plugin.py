import json
import os
from pathlib import Path
import shutil
from struct import pack
from zipfile import ZipFile
from zlib import compress, crc32

import pytest

from scripts import build_chatgpt_plugin
from scripts.build_chatgpt_plugin import build_zip, validate_package


PACKAGE = Path(__file__).resolve().parents[1] / "plugins/chatgpt/improvement-guru"
SKILL_PATH = Path("skills/qi-project-starter/SKILL.md")


@pytest.fixture
def package_copy(tmp_path):
    return shutil.copytree(PACKAGE, tmp_path / "package")


def _set_manifest_field(package, field_path, value):
    path = package / "plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    fields = manifest
    *parents, field = field_path.split("/")
    for parent in parents:
        fields = fields[parent]
    fields[field] = value
    path.write_text(json.dumps(manifest), encoding="utf-8")


def test_reviewed_plugin_package_is_valid():
    assert validate_package(PACKAGE) == []


def test_build_zip_contains_only_submission_files(tmp_path):
    path = build_zip(PACKAGE, tmp_path)

    with ZipFile(path) as archive:
        names = archive.namelist()
        assert all(name.startswith("improvement-guru/") for name in names)
        assert names == sorted(names)
        assert "improvement-guru/plugin.json" in names
        assert "improvement-guru/skills/qi-project-starter/SKILL.md" in names
        assert "improvement-guru/REVIEW_TESTS.md" not in names
        assert "improvement-guru/SUBMISSION_CHECKLIST.md" not in names
        assert all(entry.date_time == (1980, 1, 1, 0, 0, 0) for entry in archive.infolist())


def test_build_zip_is_repeatable_and_excludes_hidden_files_and_caches(package_copy, tmp_path):
    (package_copy / "assets/.DS_Store").write_bytes(b"hidden")
    cache = package_copy / "skills/__pycache__"
    cache.mkdir()
    (cache / "cached.pyc").write_bytes(b"cache")

    first = build_zip(package_copy, tmp_path / "first")
    second = build_zip(PACKAGE, tmp_path / "second")

    assert first.read_bytes() == second.read_bytes()


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("shortDescription", "x" * 31, "interface.shortDescription"),
        ("category", "Medicine", "interface.category"),
        ("brandColor", "#FFFF00", "interface.brandColor must have at least 2:1 contrast"),
        ("brandColor", "#142", "interface.brandColor must be a six-digit"),
        ("brandColorDark", "#ADD", "interface.brandColorDark must be a six-digit"),
        ("developerName", "Two\nlines", "interface.developerName must be one line"),
        ("capabilities", [" \t"], "interface.capabilities allows up to 20 non-blank"),
        ("capabilities", ["Two\nlines"], "interface.capabilities items must be one line"),
        ("defaultPrompt", [" "], "interface.defaultPrompt allows up to 3 non-blank"),
        ("defaultPrompt", ["Starter", " Starter "], "interface.defaultPrompt items must be unique"),
        ("defaultPrompt", ["Café starter", "Cafe\u0301  starter"], "interface.defaultPrompt items must be unique"),
        ("websiteURL", "https://user@example.test/", "interface.websiteURL must be an HTTPS URL"),
    ],
)
def test_invalid_listing_fields_are_reported(package_copy, field, value, expected):
    _set_manifest_field(package_copy, f"extensions/com.openai/interface/{field}", value)
    assert any(expected in error for error in validate_package(package_copy))


@pytest.mark.parametrize(
    ("field_path", "value", "expected"),
    [
        ("$schema", None, "$schema must equal"),
        ("$schema", "https://example.test/schema", "$schema must equal"),
        ("version", "1.0.0+" + "a" * 59, "version must be SemVer and at most 64"),
        ("extensions/com.openai/onboardingSkill", "./README.md", "onboardingSkill must point"),
        ("extensions/com.openai/onboardingSkill", "./skills/missing/SKILL.md", "onboardingSkill must point"),
        ("homepage", "https:///missing-host", "plugin.json.homepage must be an HTTPS URL"),
        ("homepage", "https://example.test/" + "a" * 2028, "homepage must be an HTTPS URL of at most 2048"),
        ("repository", "https://user:example@example.test", "plugin.json.repository must be an HTTPS URL"),
        ("author/url", "http://example.test", "plugin.json.author.url must be an HTTPS URL"),
        ("author/url", "https://@example.test", "plugin.json.author.url must be an HTTPS URL"),
    ],
)
def test_invalid_manifest_fields_are_reported(package_copy, field_path, value, expected):
    _set_manifest_field(package_copy, field_path, value)
    assert any(expected in error for error in validate_package(package_copy))


@pytest.mark.parametrize("key", ["mcp", "mcpServers", "apps", "hooks", "review"])
@pytest.mark.parametrize("parent", ["", "extensions/com.openai/"])
def test_component_declarations_are_rejected(package_copy, parent, key):
    _set_manifest_field(package_copy, parent + key, {})
    assert any(f"{key} is prohibited in a skills-only package" in error for error in validate_package(package_copy))


def test_missing_logo_is_reported(package_copy):
    (package_copy / "assets/logo.svg").unlink()

    assert any("interface.logo" in error for error in validate_package(package_copy))


@pytest.mark.parametrize("filename", [".mcp.json", "mcp.json"])
def test_mcp_config_blocks_validation_and_build(package_copy, tmp_path, filename):
    (package_copy / filename).write_text("{}", encoding="utf-8")
    output = tmp_path / "out"

    assert any(f"{filename} is prohibited" in error for error in validate_package(package_copy))
    with pytest.raises(ValueError, match=r"mcp\.json is prohibited"):
        build_zip(package_copy, output)
    assert not output.exists()


def test_limits_sections_must_match(package_copy):
    path = package_copy / "skills/qi-project-starter/references/worked-example.md"
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace("## Limits\n\n", "## Limits\n\nChanged text. "), encoding="utf-8")

    assert any("## Limits sections" in error for error in validate_package(package_copy))


def _png(width, height):
    def chunk(kind, payload):
        return pack(">I", len(payload)) + kind + payload + pack(">I", crc32(kind + payload))

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0))
        + chunk(b"IDAT", compress(bytes((width + 1) * height)))
        + chunk(b"IEND", b"")
    )


def _jpeg_header(width, height):
    return b"\xff\xd8\xff\xe0\x00\x02\xff\xc0" + pack(">HBHHBBBB", 11, 8, height, width, 1, 1, 0x11, 0)


def _webp_header(width, height):
    bits = width - 1 | ((height - 1) << 14)
    chunk = b"WEBPVP8L" + pack("<I", 5) + b"\x2f" + pack("<I", bits) + b"\0"
    return b"RIFF" + pack("<I", len(chunk)) + chunk


def _set_logo(package, suffix, data):
    name = f"assets/test-logo{suffix}"
    (package / name).write_bytes(data)
    _set_manifest_field(package, "extensions/com.openai/interface/logo", f"./{name}")


@pytest.mark.parametrize(
    ("suffix", "make_image"),
    [(".png", _png), (".jpg", _jpeg_header), (".jpeg", _jpeg_header), (".webp", _webp_header)],
)
def test_raster_headers_match_format_and_dimensions(package_copy, suffix, make_image):
    _set_logo(package_copy, suffix, make_image(48, 48))
    assert validate_package(package_copy) == []

    _set_logo(package_copy, suffix, make_image(48, 49))
    assert any("interface.logo image must be square" in error for error in validate_package(package_copy))

    _set_logo(package_copy, suffix, b"not an image" if suffix == ".png" else _png(48, 48))
    assert any(f"valid {suffix} image header" in error for error in validate_package(package_copy))


@pytest.mark.parametrize(
    ("side", "expected"),
    [(47, "at least 48×48"), (4097, "raster image must not exceed 4096×4096")],
)
def test_raster_dimension_limits(package_copy, side, expected):
    _set_logo(package_copy, ".jpg", _jpeg_header(side, side))
    assert any(expected in error for error in validate_package(package_copy))


def test_branding_image_size_limit(package_copy):
    _set_logo(package_copy, ".png", _png(48, 48))
    with (package_copy / "assets/test-logo.png").open("r+b") as image:
        image.truncate(5 * 1024**2 + 1)
    assert "interface.logo image must not exceed 5 MiB" in validate_package(package_copy)


def test_svg_can_use_numeric_width_and_height(package_copy):
    _set_logo(package_copy, ".svg", b'<svg width="48" height="48"/>')
    assert validate_package(package_copy) == []


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        ('width="48px" height="48px"', "must have a numeric viewBox or width and height"),
        ('width="48" height="47"', "must be square and at least 48×48"),
        ('width="47" height="47"', "must be square and at least 48×48"),
        ('viewBox="0 0 48 47" width="48" height="48"', "must be square and at least 48×48"),
    ],
)
def test_invalid_svg_dimensions_are_reported(package_copy, attributes, expected):
    _set_logo(package_copy, ".svg", f"<svg {attributes}/>".encode())
    assert any(expected in error for error in validate_package(package_copy))


@pytest.mark.skipif(os.name == "nt", reason="Windows treats backslashes as separators")
def test_zip_member_backslashes_are_rejected(package_copy):
    (package_copy / "assets" / r"bad\name.txt").touch()
    assert any("contains a backslash" in error for error in validate_package(package_copy))


def test_zip_case_collisions_are_rejected(package_copy):
    (package_copy / "assets/Collision").mkdir()
    (package_copy / "assets/Collision/Case.txt").touch()
    other = package_copy / "assets/collision/case.txt"
    other.parent.mkdir(exist_ok=True)
    if other.exists():
        # A case-insensitive filesystem cannot expose both members to rglob.
        errors = []
        first = package_copy / "assets/Collision/Case.txt"
        build_chatgpt_plugin._validate_archive_members(package_copy, [first, other], errors)
    else:
        other.touch()
        errors = validate_package(package_copy)
    assert any("collides" in error for error in errors)


def test_zip_path_depth_includes_the_plugin_directory(package_copy):
    nested = package_copy.joinpath("assets", *(["level"] * 17))
    nested.mkdir(parents=True)
    (nested / "allowed.txt").touch()
    assert validate_package(package_copy) == []

    (nested / "level").mkdir()
    (nested / "level/rejected.txt").touch()
    assert any("would exceed 20 ZIP path segments" in error for error in validate_package(package_copy))


@pytest.mark.parametrize(
    ("limit_name", "limit", "expected"),
    [
        ("MAX_MEMBER_BYTES", 0, "exceeds the 100 MiB ZIP member limit"),
        ("MAX_EXTRACTED_BYTES", 0, "Extracted ZIP must not exceed 512 MiB"),
        ("MAX_ARCHIVE_ENTRIES", 0, "ZIP must contain at most 5,000 entries"),
        ("MAX_ARCHIVE_BYTES", 0, "Compressed ZIP must not exceed 100 MB"),
    ],
)
def test_zip_limits_block_output(package_copy, tmp_path, monkeypatch, limit_name, limit, expected):
    monkeypatch.setattr(build_chatgpt_plugin, limit_name, limit)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=expected):
        build_zip(package_copy, output)
    assert not list(output.glob("*"))


@pytest.mark.parametrize("relative", [".", "assets/old-builds"])
def test_zip_output_must_be_outside_package(package_copy, relative):
    with pytest.raises(ValueError, match="outside the package root"):
        build_zip(package_copy, package_copy / relative)
    assert not list(package_copy.rglob("*.zip"))


@pytest.mark.parametrize(
    "invalid_line",
    [
        "stray text",
        "  continuation",
        "- sequence",
        "description: repeated",
        "extra: [inline, sequence]",
        "extra: >",
        "extra: text: nested mapping",
        "extra: 'quoted' trailing text",
    ],
)
def test_unparseable_frontmatter_is_rejected(package_copy, invalid_line):
    path = package_copy / SKILL_PATH
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace("\n---\n", f"\n{invalid_line}\n---\n", 1), encoding="utf-8")
    assert any("SKILL.md frontmatter line" in error for error in validate_package(package_copy))


def test_simple_quoted_frontmatter_is_accepted(package_copy):
    path = package_copy / SKILL_PATH
    content = path.read_text(encoding="utf-8")
    body = content.split("\n---\n", 1)[1]
    path.write_text(
        "---\nname: 'qi-project-starter'\ndescription: \"Draft a starter pack: QI only.\"\n"
        "extra: 'It''s a scalar' # inline comment\n---\n" + body,
        encoding="utf-8",
    )
    assert validate_package(package_copy) == []
