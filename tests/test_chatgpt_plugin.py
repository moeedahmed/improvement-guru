import json
from pathlib import Path
import shutil
from zipfile import ZipFile

import pytest

from scripts.build_chatgpt_plugin import build_zip, validate_package


PACKAGE = Path(__file__).resolve().parents[1] / "plugins/chatgpt/improvement-guru"


@pytest.fixture
def package_copy(tmp_path):
    return shutil.copytree(PACKAGE, tmp_path / "package")


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
    ],
)
def test_invalid_listing_fields_are_reported(package_copy, field, value, expected):
    path = package_copy / "plugin.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    manifest["extensions"]["com.openai"]["interface"][field] = value
    path.write_text(json.dumps(manifest), encoding="utf-8")

    assert any(expected in error for error in validate_package(package_copy))


def test_missing_logo_is_reported(package_copy):
    (package_copy / "assets/logo.svg").unlink()

    assert any("interface.logo" in error for error in validate_package(package_copy))


def test_mcp_config_blocks_validation_and_build(package_copy, tmp_path):
    (package_copy / ".mcp.json").write_text("{}", encoding="utf-8")
    output = tmp_path / "out"

    assert any(".mcp.json is prohibited" in error for error in validate_package(package_copy))
    with pytest.raises(ValueError, match=r"\.mcp\.json is prohibited"):
        build_zip(package_copy, output)
    assert not output.exists()


def test_limits_sections_must_match(package_copy):
    path = package_copy / "skills/qi-project-starter/references/worked-example.md"
    content = path.read_text(encoding="utf-8")
    path.write_text(content.replace("## Limits\n\n", "## Limits\n\nChanged text. "), encoding="utf-8")

    assert any("## Limits sections" in error for error in validate_package(package_copy))
