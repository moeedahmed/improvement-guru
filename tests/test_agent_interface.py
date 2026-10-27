"""Agent-connection contract: any agent driving the CLI keeps getting the documented answers.

The cases in golden/agent_answers.json are good example answers for each documented
command. They run in order against the installed command line (a real subprocess, as an
agent would call it), share one temporary folder, and use only the synthetic examples.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_usage_error_exits_2_with_help_on_stderr(tmp_path):
    result = _run([], tmp_path)

    assert result.returncode == 2
    assert result.stdout == ""
    assert "usage: improvement-guru" in result.stderr


def test_every_documented_command_is_listed_in_help(tmp_path):
    help_text = _run(["--help"], tmp_path).stdout
    documented = re.findall(r"^\| `improvement-guru (\w+)", INTERFACE_DOC, flags=re.MULTILINE)

    assert set(documented) == {"new", "sources", "charts", "deid"}
    for command in documented:
        assert command in help_text


def test_documented_exit_codes_match_the_cases():
    assert {case["exit_code"] for case in CASES} == {0, 1, 2}
    for code in ("0", "1", "2"):
        assert re.search(rf"^\| {code} \|", INTERFACE_DOC, flags=re.MULTILINE)
