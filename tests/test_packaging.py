import tomllib
from pathlib import Path

from improvement_guru.cli import _build_parser
from improvement_guru.paths import INSTALLED_DATA_ROOT


def test_public_distribution_identity_matches_release_decision():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert pyproject["project"]["name"] == "improvement-guru"
    assert pyproject["project"]["version"] == "0.1.0rc1"
    assert pyproject["project"]["scripts"] == {"improvement-guru": "improvement_guru.cli:main"}
    assert pyproject["tool"]["setuptools"]["packages"]["find"]["include"] == ["improvement_guru*"]
    assert set(pyproject["tool"]["setuptools"]["data-files"]) == {
        "improvement-guru/checklists",
        "improvement-guru/examples",
        "improvement-guru/skills",
        "improvement-guru/standards",
        "improvement-guru/templates",
    }
    assert INSTALLED_DATA_ROOT.name == "improvement-guru"


def test_cli_help_uses_installed_command_name():
    parser = _build_parser()

    assert parser.prog == "improvement-guru"
