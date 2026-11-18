"""Project record contracts using synthetic aggregate data only."""

from datetime import date, timedelta
import json

import pytest

from improvement_guru import project
from improvement_guru.cli import main
from improvement_guru.scaffold import create_project


@pytest.fixture
def directory(tmp_path):
    path = tmp_path / "synthetic_project"
    create_project(path, date="2026-01-05")
    return path


def run(directory, command, *arguments):
    return main(["project", command, str(directory), *arguments])


def ready_record():
    record = project.new_record("Synthetic project", "2026-01-05")
    record.update(route="qi", aim="Improve synthetic completion by ten percentage points within eight weeks.")
    record["measures"] = [dict(name=kind, kind=kind, definition="Synthetic weekly proportion") for kind in project.KINDS]
    return record


def test_record_round_trip_and_new_cli(tmp_path, capsys):
    directory = tmp_path / "synthetic"
    assert main(["new", str(directory)]) == 0
    record = project.load_record(directory)
    assert record == project.new_record("synthetic", date.today().isoformat())
    assert "project.json" in capsys.readouterr().out
    assert record["route"] is None
    assert record["audit"] == {}


def test_atomic_replace_failure_leaves_original_and_no_temp(directory, monkeypatch):
    path = directory / "project.json"
    original = path.read_bytes()
    record = project.load_record(directory)
    record["aim"] = "Synthetic aim"

    def fail_replace(source, target):
        assert target == path
        assert project.load_record(directory)["aim"] == ""
        assert json.loads(source.read_text())["aim"] == "Synthetic aim"
        raise OSError("injected replace failure")

    monkeypatch.setattr(project.os, "replace", fail_replace)
    with pytest.raises(OSError, match="injected"):
        project.write_record(directory, record)
    assert path.read_bytes() == original
    assert not list(directory.glob(".project-*.tmp"))


def test_atomic_write_failure_leaves_original(directory, monkeypatch):
    original = (directory / "project.json").read_bytes()
    def fail_sync(_fd):
        raise OSError("injected flush failure")
    monkeypatch.setattr(project.os, "fsync", fail_sync)
    assert run(directory, "set-aim", "--aim", "Synthetic aim") == 2
    assert (directory / "project.json").read_bytes() == original
    assert not (directory / ".project.lock").exists()
    assert not list(directory.glob(".project-*.tmp"))


def test_concurrent_writer_refused(directory):
    with project.edit_record(directory) as record:
        assert run(directory, "set-aim", "--aim", "Competing aim") == 2
        record["aim"] = "First writer"
    assert project.load_record(directory)["aim"] == "First writer"


def test_edit_commands(directory):
    assert run(directory, "set-aim", "--aim", "Synthetic SMART aim") == 0
    assert run(directory, "set-route", "--route", "service-evaluation") == 0
    assert run(directory, "set-stage", "--stage", "test") == 0
    assert run(directory, "add-measure", "--name", "Completion", "--kind", "outcome") == 0
    assert run(directory, "add-measure", "--name", "Completion", "--kind", "outcome", "--definition", "Weekly completion proportion") == 0
    assert run(directory, "add-pdsa", "--change-idea", "Synthetic prompt", "--prediction", "Completion rises") == 0
    assert run(directory, "close-pdsa", "--id", "1", "--result", "Completion rose", "--decision", "adapt") == 0
    record = project.load_record(directory)
    assert record["aim"] == "Synthetic SMART aim"
    assert record["route"] == "service-evaluation"
    assert record["stage"] == "test"
    assert record["measures"] == [dict(name="Completion", kind="outcome", definition="Weekly completion proportion")]
    assert record["pdsa_cycles"] == [dict(id=1, change_idea="Synthetic prompt", prediction="Completion rises", result="Completion rose", decision="adapt")]
    assert run(directory, "add-pdsa", "--change-idea", "Revised prompt", "--prediction", "Further rise") == 0
    assert project.load_record(directory)["pdsa_cycles"][-1]["id"] == 2


@pytest.mark.parametrize("arguments", [
    ["set-aim", "--aim", " "],
    ["add-measure", "--name", " ", "--kind", "process"],
    ["add-pdsa", "--change-idea", "Prompt", "--prediction", " "],
    ["close-pdsa", "--id", "88", "--result", "No result", "--decision", "adopt"],
])
def test_invalid_edit_does_not_write(directory, arguments):
    original = (directory / "project.json").read_bytes()
    assert run(directory, arguments[0], *arguments[1:]) == 2
    assert (directory / "project.json").read_bytes() == original


@pytest.mark.parametrize("command, arguments", [
    ("set-route", ["--route", "automatic"]),
    ("set-stage", ["--stage", "finished"]),
    ("add-measure", ["--name", "Synthetic", "--kind", "other"]),
    ("add-pdsa", ["--change-idea", "Prompt"]),
    ("close-pdsa", ["--id", "1", "--result", "Result", "--decision", "open"]),
    ("add-counts", ["--week", "2026-01-05", "--numerator", "1.5", "--denominator", "2"]),
])
def test_parser_rejects_invalid_values(directory, command, arguments):
    with pytest.raises(SystemExit) as error:
        run(directory, command, *arguments)
    assert error.value.code == 2


@pytest.mark.parametrize("stage", project.STAGES)
def test_next_always_requires_confirmed_route(stage):
    record = ready_record()
    record.update(route=None, stage=stage)
    step, reason = project.next_step(record)
    assert step.startswith("Confirm with your local QI/audit/governance team")
    assert "not been confirmed" in reason


def test_next_aim_measure_kinds_and_definition():
    record = ready_record()
    record["aim"] = ""
    assert "SMART aim" in project.next_step(record)[0]
    record["aim"] = "Synthetic aim"
    for kind in project.KINDS:
        original = record["measures"]
        record["measures"] = [item for item in original if item["kind"] != kind]
        assert f"Add a {kind} measure" in project.next_step(record)[0]
        record["measures"] = original
    record["measures"][2]["definition"] = ""
    assert "Define the measure 'balancing'" in project.next_step(record)[0]


@pytest.mark.parametrize("stage", ["start", "test"])
def test_next_test_branches(stage):
    record = ready_record()
    record["stage"] = stage
    assert "prediction" in project.next_step(record)[0]
    record["pdsa_cycles"] = [dict(id=1, change_idea="Prompt", prediction="Rise", result="", decision="open")]
    assert "against its prediction" in project.next_step(record)[0]
    record["pdsa_cycles"][0].update(result="Rise observed", decision="adopt")
    assert "stage to measure" in project.next_step(record)[0]


def test_next_measure_branches():
    record = ready_record()
    record["stage"] = "measure"
    assert "Keep collecting" in project.next_step(record)[0]
    record["weekly_counts"] = [dict(week=(date(2026, 1, 5) + timedelta(weeks=i)).isoformat(), numerator=value, denominator=10) for i, value in enumerate([1] * 6 + [9] * 6)]
    step, reason = project.next_step(record)
    assert "named run-chart signal" in step
    assert "Shift signal:" in reason
    assert "not proof" in reason
    for i, point in enumerate(record["weekly_counts"]):
        point["numerator"] = 1 if i % 2 else 9
    step, reason = project.next_step(record)
    assert "next small test" in step
    assert "No Shift or Trend signal" in reason


@pytest.mark.parametrize("route, stage", [("audit", "start"), ("qi", "audit")])
def test_next_audit_branches(route, stage):
    record = ready_record()
    record.update(route=route, stage=stage)
    for key in ("standard", "source", "sample_rules", "baseline_compliance", "reeaudit_date"):
        assert key.replace("_", " ") in project.next_step(record)[0]
        record["audit"][key] = "2026-06-01" if key == "reeaudit_date" else "Synthetic audit detail"
    assert "re-audit against the same standard" in project.next_step(record)[0]
    record["stage"] = "write-up"
    assert "Write up" in project.next_step(record)[0]


def test_next_write_up_and_research():
    record = ready_record()
    record["stage"] = "write-up"
    assert "Write up" in project.next_step(record)[0]
    record["route"] = "research"
    assert "research protocol" in project.next_step(record)[0]


def test_next_cli_default_directory_and_disclaimer(directory, monkeypatch, capsys):
    monkeypatch.chdir(directory)
    assert main(["project", "next"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 3
    assert lines[1].startswith("Reason:")
    assert lines[-1] == project.DISCLAIMER


@pytest.mark.parametrize("numerator, denominator", [(-1, 10), (0, 0), (2, 1), (0, -1)])
def test_invalid_counts_do_not_write(directory, numerator, denominator):
    original = (directory / "project.json").read_bytes()
    assert run(directory, "add-counts", "--week", "2026-01-05", "--numerator", str(numerator), "--denominator", str(denominator)) == 2
    assert (directory / "project.json").read_bytes() == original


@pytest.mark.parametrize("week", ["2026-02-30", "20260105", "2026-1-5", "1980-01-05 extra", "999 000 0018", "synthetic@example.invalid"])
def test_invalid_week_does_not_write(directory, week):
    original = (directory / "project.json").read_bytes()
    assert run(directory, "add-counts", "--week", week, "--numerator", "1", "--denominator", "2") == 2
    assert (directory / "project.json").read_bytes() == original


def test_counts_success_duplicate_and_order(directory, capsys):
    assert run(directory, "add-counts", "--week", "2026-01-12", "--numerator", "1", "--denominator", "2") == 0
    output = capsys.readouterr().out
    assert "Weekly proportion: 0.5" in output
    assert "too few points (0 of at least 10)" in output
    assert "run chart, not SPC" in output
    assert run(directory, "add-counts", "--week", "2026-01-05", "--numerator", "0", "--denominator", "2") == 0
    original = (directory / "project.json").read_bytes()
    assert run(directory, "add-counts", "--week", "2026-01-05", "--numerator", "0", "--denominator", "2") == 2
    assert (directory / "project.json").read_bytes() == original
    assert len(project.load_record(directory)["weekly_counts"]) == 2


@pytest.mark.parametrize("identifier", ["1980-01-05", "999 000 0018", "synthetic@example.invalid"])
@pytest.mark.parametrize("location", ["aim", "name", "definition", "measure_name", "change_idea", "prediction", "result", "audit", "unknown"])
def test_counts_deid_refuses_all_text_and_final_content(directory, capsys, identifier, location):
    record = project.load_record(directory)
    if location in ("definition", "measure_name"):
        record["measures"] = [dict(name=identifier if location == "measure_name" else "Completion", kind="outcome", definition=identifier if location == "definition" else "Weekly proportion")]
    elif location in ("change_idea", "prediction", "result"):
        cycle = dict(id=1, change_idea="Prompt", prediction="Rise", result="Rise observed", decision="adopt")
        cycle[location] = identifier
        record["pdsa_cycles"] = [cycle]
    elif location == "audit":
        record["audit"]["standard"] = identifier
    else:
        record[location] = identifier
    project.write_record(directory, record)
    original = (directory / "project.json").read_bytes()
    week = "2026-01-05"
    assert run(directory, "add-counts", "--week", week, "--numerator", "1", "--denominator", "2") == 1
    output = capsys.readouterr().err
    assert "assistive and not a guarantee" in output
    assert identifier not in output
    assert (directory / "project.json").read_bytes() == original
    assert not (directory / ".project.lock").exists()


@pytest.mark.parametrize("content", ['{', '[]', '{"schema_version": 7}', '{}'])
def test_invalid_record_is_clear_error(directory, capsys, content):
    (directory / "project.json").write_text(content)
    assert run(directory, "next") == 2
    assert "Error:" in capsys.readouterr().err
    assert (directory / "project.json").read_text() == content


def test_missing_record_is_clear_error(tmp_path, capsys):
    assert run(tmp_path, "next") == 2
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("audit_date_key", ["reeaudit_date", "reaudit_date"])
def test_counts_accepts_structured_dates(directory, audit_date_key):
    record = project.load_record(directory)
    record["created"] = date.today().isoformat()
    record["audit"][audit_date_key] = "2026-06-01"
    project.write_record(directory, record)
    assert run(directory, "add-counts", "--week", "2026-01-05", "--numerator", "1", "--denominator", "2") == 0
    saved = project.load_record(directory)
    assert saved["created"] == record["created"]
    assert saved["audit"] == record["audit"]
    assert saved["weekly_counts"] == [dict(week="2026-01-05", numerator=1, denominator=2)]


@pytest.mark.parametrize("field", ["created", "reeaudit_date", "reaudit_date"])
@pytest.mark.parametrize("value", ["2026-02-30", "20260105", "2026-1-5", "1980-01-05 synthetic@example.invalid"])
def test_structured_dates_are_strictly_validated(directory, field, value):
    path = directory / "project.json"
    record = project.load_record(directory)
    target = record if field == "created" else record["audit"]
    target[field] = value
    path.write_text(json.dumps(record))
    original = path.read_bytes()
    assert run(directory, "add-counts", "--week", "2026-01-05", "--numerator", "1", "--denominator", "2") == 2
    assert path.read_bytes() == original


@pytest.mark.parametrize("identifier", ["1980-01-05", "999 000 0018", "synthetic@example.invalid"])
def test_counts_scans_directory_arg(directory, identifier):
    target = directory.rename(directory.with_name(identifier))
    original = (target / "project.json").read_bytes()
    assert run(target, "add-counts", "--week", "2026-01-05", "--numerator", "1", "--denominator", "2") == 1
    assert (target / "project.json").read_bytes() == original
    assert not (target / ".project.lock").exists()


def test_counts_reports_named_rules_in_week_order(directory, capsys):
    record = project.load_record(directory)
    record["weekly_counts"] = [dict(week=(date(2026, 1, 5) + timedelta(weeks=i)).isoformat(), numerator=value, denominator=100) for i, value in enumerate([1] * 6 + [10, 20, 30, 40, 50])]
    record["weekly_counts"].reverse()
    project.write_record(directory, record)
    assert run(directory, "add-counts", "--week", (date(2026, 1, 5) + timedelta(weeks=11)).isoformat(), "--numerator", "60", "--denominator", "100") == 0
    output = capsys.readouterr().out
    assert "Shift signal: 6 points above" in output
    assert "Trend signal: 5 points going up" in output
    assert "not proof" in output


def test_zero_audit_baseline_is_present():
    record = ready_record()
    record["route"] = "audit"
    record["audit"] = dict(standard="Synthetic standard", source="Synthetic source", sample_rules="Synthetic sampling", baseline_compliance=0)
    assert "reeaudit date" in project.next_step(record)[0]


def test_scaffold_record_failure_rolls_back(tmp_path, monkeypatch):
    import improvement_guru.scaffold as scaffold
    def fail_write(*args):
        raise OSError("injected record failure")
    monkeypatch.setattr(scaffold, "write_record", fail_write)
    directory = tmp_path / "synthetic_failure"
    with pytest.raises(OSError, match="injected"):
        create_project(directory)
    assert not directory.exists()
