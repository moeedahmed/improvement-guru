"""Agent-connection contract: any agent driving the CLI keeps getting the documented answers.

The cases in golden/agent_answers.json are good example answers for each documented
command. They run in order against the installed command line (a real subprocess, as an
agent would call it), share one temporary folder, and use only the synthetic examples.
"""

import errno
import json
import os
import re
import subprocess
import sys
import tomllib
from importlib import metadata
from pathlib import Path

import pytest

import improvement_guru.cli as cli
import improvement_guru.sources as sources
from improvement_guru.cli import main

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "tests" / "golden" / "agent_answers.json").read_text(encoding="utf-8"))
INTERFACE_DOC = (ROOT / "docs" / "AGENT_INTERFACE.md").read_text(encoding="utf-8")


def _run(args, cwd):
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        [sys.executable, "-m", "improvement_guru", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )


@pytest.fixture(scope="module")
def workdir(tmp_path_factory):
    return tmp_path_factory.mktemp("agent-interface")


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_agent_receives_documented_answer(case, workdir):
    args = [
        part.replace("{tmp}", str(workdir)).replace("{examples}", str(ROOT / "examples"))
        for part in case["args"]
    ]

    result = _run(args, workdir)

    assert result.returncode == case["exit_code"], result.stderr
    assert re.search(case["stdout_regex"], result.stdout), result.stdout
    assert re.search(case["stderr_regex"], result.stderr), result.stderr


def test_no_command_exits_2_with_top_level_help(tmp_path):
    result = _run([], tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == _run(["--help"], tmp_path).stdout


@pytest.mark.parametrize("args", [["new"], ["invalid-command"]])
def test_argparse_usage_error_exits_2(tmp_path, args):
    result = _run(args, tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith("usage: improvement-guru")
    assert re.match(r"^improvement-guru(?: new)?: error: ", result.stderr.splitlines()[-1])


@pytest.mark.parametrize("group", ["deid", "charts", "sources"])
def test_bare_group_prints_its_own_help(tmp_path, group):
    result = _run([group], tmp_path)
    help_result = _run([group, "--help"], tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr.startswith(f"usage: improvement-guru {group}")
    assert result.stderr == help_result.stdout


def test_run_chart_help_includes_threshold_defaults(tmp_path):
    result = _run(["charts", "run-chart", "--help"], tmp_path)

    assert result.returncode == 0
    run_help = result.stdout.rsplit("--run-length RUN_LENGTH", 1)[1]
    run_help, trend_help = run_help.split("--trend-length TREND_LENGTH", 1)
    assert "(default: 6)" in " ".join(run_help.split())
    assert "(default: 5)" in " ".join(trend_help.split())


def test_version_matches_package_version(tmp_path):
    try:
        version = metadata.version("improvement-guru")
    except metadata.PackageNotFoundError:
        with (ROOT / "pyproject.toml").open("rb") as handle:
            version = tomllib.load(handle)["project"]["version"]

    result = _run(["--version"], tmp_path)

    assert result.returncode == 0
    assert result.stdout == f"improvement-guru {version}\n"
    assert result.stderr == ""


def test_version_prefers_installed_metadata(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "SOURCE_ROOT", tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "foreign"\nversion = "8.0.0"\n', encoding="utf-8"
    )

    def installed_version(name):
        assert name == "improvement-guru"
        return "9.0.0"

    monkeypatch.setattr(metadata, "version", installed_version)

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr() == ("improvement-guru 9.0.0\n", "")


@pytest.mark.parametrize(
    "version", [None, " \t", 123, "1.2.3\r"], ids=["missing", "blank", "not-a-string", "carriage-return"]
)
def test_version_rejects_invalid_installed_metadata(monkeypatch, capsys, version):
    monkeypatch.setattr(metadata, "version", lambda name: version)

    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 2
    assert capsys.readouterr() == ("", "Error: could not determine the improvement-guru version\n")


@pytest.mark.parametrize(
    "version_header", [b"1.2.3\xff", b"1.2.3\n continued"], ids=["invalid-utf8", "folded"]
)
def test_version_rejects_invalid_dist_info(tmp_path, monkeypatch, capsys, version_header):
    dist_info = tmp_path / "improvement_guru-1.2.3.dist-info"
    dist_info.mkdir()
    (dist_info / "METADATA").write_bytes(
        b"Metadata-Version: 2.1\nName: improvement-guru\nVersion: " + version_header + b"\n"
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    with pytest.raises(SystemExit) as exc:
        main(["--version"])

    assert exc.value.code == 2
    assert capsys.readouterr() == ("", "Error: could not determine the improvement-guru version\n")


@pytest.mark.parametrize(
    ("toml", "expected"),
    [
        ('[project]\nname = "improvement-guru"\nversion = "1.2.3"', "1.2.3"),
        ('[project]\nname = "foreign"\nversion = "1.2.3"', None),
        ("[project", None),
        ('[project]\nname = "improvement-guru"', None),
        ('[project]\nname = "improvement-guru"\nversion = ""', None),
        ('[project]\nname = "improvement-guru"\nversion = 123', None),
        (None, None),
    ],
)
def test_version_without_installed_metadata(tmp_path, monkeypatch, capsys, toml, expected):
    monkeypatch.setattr(cli, "SOURCE_ROOT", tmp_path)
    if toml is not None:
        (tmp_path / "pyproject.toml").write_text(toml, encoding="utf-8")

    def missing_version(name):
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "version", missing_version)

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    captured = capsys.readouterr()
    if expected is None:
        assert exc.value.code == 2
        assert captured == ("", "Error: could not determine the improvement-guru version\n")
    else:
        assert exc.value.code == 0
        assert captured == (f"improvement-guru {expected}\n", "")


@pytest.mark.parametrize("command", ["scan", "redact"])
@pytest.mark.parametrize(
    ("problem", "reason"),
    [
        ("missing", None),
        ("directory", None),
        ("encoding", "is not valid UTF-8 text; save the file as CSV UTF-8 and try again"),
    ],
)
def test_deid_invalid_input_is_a_single_error(tmp_path, command, problem, reason):
    source = tmp_path / "input.csv"
    destination = tmp_path / "output.csv"
    if problem == "directory":
        source.mkdir()
    elif problem == "encoding":
        source.write_bytes("label\ncafé\n".encode("latin-1"))
    args = ["deid", command, str(source)]
    if command == "redact":
        args.extend(["--out", str(destination)])

    result = _run(args, tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert len(result.stderr.splitlines()) == 1
    assert result.stderr.startswith("Error: ")
    assert "[Errno" not in result.stderr
    assert repr(str(source)) in result.stderr
    if reason is not None:
        assert result.stderr.rstrip().endswith(reason)
    assert not destination.exists()


@pytest.mark.parametrize("command", ["scan", "redact"])
def test_deid_unreadable_input_is_a_single_error(tmp_path, monkeypatch, capsys, command):
    source = tmp_path / "input.csv"
    source.write_text("label\nsynthetic\n", encoding="utf-8")
    destination = tmp_path / "output.csv"
    original_open = Path.open

    def deny_input(path, *args, **kwargs):
        if path == source:
            raise PermissionError(errno.EACCES, "Permission denied", str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_input)
    args = ["deid", command, str(source)]
    if command == "redact":
        args.extend(["--out", str(destination)])

    assert main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err.splitlines()) == 1
    assert captured.err.startswith("Error: ")
    assert repr(str(source)) in captured.err
    assert not destination.exists()


@pytest.mark.parametrize("loop_path", ["./input.csv", "./output.csv"])
def test_redact_reports_symlink_loop_at_typed_path(monkeypatch, capsys, loop_path):
    original_resolve = Path.resolve

    def resolve(path, *args, **kwargs):
        if path == Path(loop_path):
            raise RuntimeError("injected symlink loop")
        return original_resolve(path, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", resolve)

    assert main(["deid", "redact", "./input.csv", "--out", "./output.csv"]) == 2
    assert capsys.readouterr() == ("", f"Error: symlink loop in path: {loop_path!r}\n")


@pytest.mark.parametrize(
    ("name", "message"),
    [
        ("", "project name is empty"),
        ("sub/dir/p3", f"parent folder does not exist: {Path('sub/dir')}"),
    ],
)
def test_new_invalid_project_path_is_a_single_error(tmp_path, name, message):
    result = _run(["new", name], tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == f"Error: {message}\n"
    assert not list(tmp_path.iterdir())


def test_new_unwritable_parent_is_a_single_error(tmp_path, monkeypatch, capsys):
    target = tmp_path / "project"
    original_mkdir = Path.mkdir

    def deny_project(path, *args, **kwargs):
        if path == target:
            raise PermissionError(errno.EACCES, "Permission denied", str(path))
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", deny_project)

    assert main(["new", str(target)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert len(captured.err.splitlines()) == 1
    assert captured.err.startswith("Error: ")
    assert repr(str(target)) in captured.err
    assert not target.exists()


@pytest.mark.parametrize(
    ("filename", "message"),
    [
        ("global.json", "could not read source profile: 'global'"),
        ("pdsa-log.md", "could not read scaffold template: pdsa-log.md"),
    ],
)
@pytest.mark.parametrize("failure", ["io", "io-without-filename", "utf8"])
def test_new_reports_bundled_read_failure(tmp_path, monkeypatch, capsys, filename, message, failure):
    target = tmp_path / "project"
    original_open = Path.open

    def fail_read(path, *args, **kwargs):
        if path.name == filename:
            if failure == "utf8":
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            if failure == "io-without-filename":
                raise OSError(errno.EIO, "injected read failure")
            raise PermissionError(errno.EACCES, "injected read failure", str(path))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_read)

    assert main(["new", str(target)]) == 2
    assert capsys.readouterr() == ("", f"Error: {message}\n")
    assert not target.exists()


@pytest.mark.parametrize("contents", ["{", "{}"], ids=["invalid-json", "invalid-schema"])
def test_new_reports_malformed_bundled_profile(tmp_path, monkeypatch, capsys, contents):
    target = tmp_path / "project"
    monkeypatch.setattr(json, "load", lambda handle: json.loads(contents))

    assert main(["new", str(target)]) == 2
    assert capsys.readouterr() == ("", "Error: could not read source profile: 'global'\n")
    assert not target.exists()


@pytest.mark.parametrize("regular_file", [False, True], ids=["absent", "regular-file"])
def test_sources_list_reports_missing_profile_folder(tmp_path, monkeypatch, capsys, regular_file):
    standards = tmp_path / "standards"
    if regular_file:
        standards.touch()
    monkeypatch.setattr(sources, "STANDARDS_DIR", standards)

    assert main(["sources", "list"]) == 2
    assert capsys.readouterr() == ("", "Error: source profile folder is missing\n")


@pytest.mark.parametrize("args", [["list"], ["show", "global"]], ids=["list", "show"])
def test_sources_propagates_stdout_encoding_error(monkeypatch, args):
    def fail_on_stdout(message, *, file=None):
        if file is None:
            raise UnicodeEncodeError("ascii", "é", 0, 1, "injected write failure")
        print(message, file=file)

    monkeypatch.setattr(cli, "print", fail_on_stdout, raising=False)

    with pytest.raises(UnicodeEncodeError):
        main(["sources", *args])


@pytest.mark.parametrize(
    "args", [["new", "project", "--profile", "unknown"], ["sources", "list"], ["sources", "show", "australia"]],
    ids=["new-unknown", "sources-list", "sources-show"],
)
@pytest.mark.parametrize("failure", ["malformed-json", "unreadable"])
def test_cli_names_the_bundled_profile_that_failed(tmp_path, monkeypatch, capsys, args, failure):
    profile = tmp_path / "australia.json"
    profile.write_text("{", encoding="utf-8")
    monkeypatch.setattr(sources, "STANDARDS_DIR", tmp_path)
    monkeypatch.chdir(tmp_path)
    if failure == "unreadable":
        original_open = Path.open

        def fail_profile_read(path, *args, **kwargs):
            if path == profile:
                raise PermissionError(errno.EACCES, "injected read failure", str(path))
            return original_open(path, *args, **kwargs)

        monkeypatch.setattr(Path, "open", fail_profile_read)

    assert main(args) == 2
    assert capsys.readouterr() == ("", "Error: could not read source profile: 'australia'\n")
    assert not (tmp_path / "project").exists()


@pytest.mark.parametrize("separator", [";", "\t"])
@pytest.mark.parametrize("column_kind", ["value", "date"])
def test_run_chart_missing_column_suggests_comma_delimited_csv(tmp_path, separator, column_kind):
    source = tmp_path / "input.csv"
    destination = tmp_path / "output.csv"
    header = f"week{separator}measure"
    row = f"one{separator}5"
    value_column = "missing"
    if column_kind == "date":
        header = f"count,{header}"
        row = f"1,{row}"
        value_column = "count"
    source.write_text(f"{header}\n{row}\n", encoding="utf-8")
    args = ["charts", "run-chart", str(source), "--value-column", value_column, "--out", str(destination)]
    if column_kind == "date":
        args.extend(["--date-column", "missing"])

    result = _run(args, tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        f"Error: {column_kind} column not found: missing; "
        "the file may not be comma-separated; save it as CSV (comma delimited)\n"
    )
    assert not destination.exists()


def test_every_documented_command_is_listed_in_help(tmp_path):
    help_text = _run(["--help"], tmp_path).stdout
    documented = re.findall(r"^\| `improvement-guru (--version|\w+)", INTERFACE_DOC, flags=re.MULTILINE)

    assert set(documented) == {"--version", "new", "sources", "charts", "deid"}
    for command in documented:
        assert command in help_text


def test_documented_exit_codes_match_the_cases():
    assert {case["exit_code"] for case in CASES} == {0, 1, 2}
    for code in ("0", "1", "2"):
        assert re.search(rf"^\| {code} \|", INTERFACE_DOC, flags=re.MULTILINE)


@pytest.mark.parametrize("stdout_tty,stderr_tty", [(False, True), (True, False), (False, False), (True, True)])
def test_new_terminal_guidance(tmp_path, monkeypatch, capsys, stdout_tty, stderr_tty):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: stdout_tty)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: stderr_tty)
    folder = Path("ward_review")
    args = ["new", str(folder), "--profile", "canada"]
    assert main(args) == 0
    output = capsys.readouterr()
    filenames = (
        "charter.md", "pdsa-log.md", "driver-diagram.md", "data-collection-spec.md",
        "audit-standards.md", "ig-caldicott.md", "deid-checklist.md", "qip-registration.md", "source-map.md",
    )
    assert output.out == "".join(f"{folder / name}\n" for name in filenames)
    guidance = (
        "Created 9 files in ward_review (profile: canada).\nNext:\n"
        f"1. Open {folder / 'charter.md'} and write your aim.\n"
        f"2. Read {folder / 'source-map.md'} for the sources behind this profile.\n"
        "3. Before collecting data, confirm your local governance route and review the "
        "registration, information-governance and de-identification checklists.\n"
        "Keep patient-identifiable data out of this toolkit.\n"
    )
    assert output.err == (guidance if stdout_tty and stderr_tty else "")


def test_new_terminal_guidance_prints_normalised_profile(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)

    assert main(["new", "ward_review", "--profile", " UK "]) == 0
    assert capsys.readouterr().err.splitlines()[0] == (
        "Created 9 files in ward_review (profile: uk)."
    )


def test_new_failure_in_terminal(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    monkeypatch.setattr(sys.stderr, "isatty", lambda: True)
    assert main(["new", str(tmp_path)]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == f"Error: project folder already exists: {tmp_path}\n"
