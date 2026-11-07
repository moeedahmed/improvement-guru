"""Local project records and deterministic guidance for doctors' QI work."""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from datetime import date
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from improvement_guru import deid
from improvement_guru.charts import RUN_CHART_CAUTION, analyse_series

ROUTES = ("audit", "service-evaluation", "qi", "research")
STAGES = ("start", "test", "measure", "audit", "write-up")
KINDS = ("outcome", "process", "balancing")
DECISIONS = ("adopt", "adapt", "abandon", "open")
DISCLAIMER = (
    "Not clinical decision support or governance approval. "
    "Confirm your route and register the project locally."
)


class IdentifierRefusal(ValueError):
    """The assistive scanner flagged content that must not be saved."""


def new_record(name: str, created: str) -> dict:
    record = dict(
        schema_version=1, name=name, created=created, route=None, stage="start",
        aim="", measures=[], pdsa_cycles=[], weekly_counts=[], audit={},
    )
    validate_record(record)
    return record


def _text(value: object, field: str, *, empty: bool = False) -> None:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise ValueError(f"{field} must be {'text' if empty else 'non-empty text'}")


def _date(value: object, field: str) -> None:
    _text(value, field)
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a valid YYYY-MM-DD date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must be a valid YYYY-MM-DD date")


def validate_counts(numerator: int, denominator: int) -> None:
    if type(numerator) is not int or type(denominator) is not int:
        raise ValueError("numerator and denominator must be whole numbers")
    if numerator < 0 or denominator <= 0 or numerator > denominator:
        raise ValueError("counts require 0 <= numerator <= denominator and denominator > 0")


def validate_record(record: dict) -> None:
    """Validate stored records as well as CLI edits, before any write."""
    if not isinstance(record, dict) or type(record.get("schema_version")) is not int or record["schema_version"] != 1:
        raise ValueError("unsupported project schema_version (expected 1)")
    _text(record.get("name"), "name")
    _date(record.get("created"), "created")
    if record.get("route") not in (None, *ROUTES):
        raise ValueError("invalid project route")
    if record.get("stage") not in STAGES:
        raise ValueError("invalid project stage")
    _text(record.get("aim"), "aim", empty=True)
    for key in ("measures", "pdsa_cycles", "weekly_counts"):
        if not isinstance(record.get(key), list) or any(not isinstance(item, dict) for item in record[key]):
            raise ValueError(f"{key} must be a list of objects")
    for measure in record["measures"]:
        _text(measure.get("name"), "measure name")
        if measure.get("kind") not in KINDS:
            raise ValueError("invalid measure kind")
        _text(measure.get("definition"), "measure definition", empty=True)
    ids = set()
    for cycle in record["pdsa_cycles"]:
        if type(cycle.get("id")) is not int or cycle["id"] < 1 or cycle["id"] in ids:
            raise ValueError("PDSA ids must be unique positive whole numbers")
        ids.add(cycle["id"])
        _text(cycle.get("change_idea"), "change idea")
        _text(cycle.get("prediction"), "prediction")
        if cycle.get("decision") not in DECISIONS:
            raise ValueError("invalid PDSA decision")
        _text(cycle.get("result"), "result", empty=cycle["decision"] == "open")
    weeks = set()
    for point in record["weekly_counts"]:
        _date(point.get("week"), "week")
        validate_counts(point.get("numerator"), point.get("denominator"))
        if point["week"] in weeks:
            raise ValueError("only one count per week is allowed")
        weeks.add(point["week"])
    audit = record.get("audit")
    if not isinstance(audit, dict):
        raise ValueError("audit must be an object")
    for key in ("standard", "source", "sample_rules"):
        if audit.get(key) is not None:
            _text(audit[key], f"audit {key}", empty=True)
    baseline = audit.get("baseline_compliance")
    if isinstance(baseline, str):
        _text(baseline, "audit baseline_compliance", empty=True)
    elif baseline is not None and (type(baseline) not in (int, float) or not math.isfinite(baseline)):
        raise ValueError("audit baseline_compliance must be text or a finite number")
    for key in ("reeaudit_date", "reaudit_date"):
        if audit.get(key) is not None:
            _date(audit[key], key)


def load_record(directory: str | Path) -> dict:
    try:
        record = json.loads((Path(directory) / "project.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("project.json is not valid JSON") from exc
    validate_record(record)
    return record


def serialise(record: dict) -> str:
    validate_record(record)
    return json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def write_record(directory: str | Path, record: dict) -> None:
    """Replace a complete record atomically, cleaning up even on failure."""
    content = serialise(record)
    temporary = None
    try:
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory,
                                prefix=".project-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, Path(directory) / "project.json")
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def edit_record(directory: str | Path):
    """Reject concurrent writers instead of losing an update."""
    lock = Path(directory) / ".project.lock"
    try:
        lock.mkdir()
    except FileExistsError as exc:
        raise ValueError("project is being edited (.project.lock exists); retry after the edit finishes") from exc
    try:
        record = load_record(directory)
        yield record
        write_record(directory, record)
    finally:
        lock.rmdir()


def check_identifiers(text: str) -> None:
    if deid.scan_text(text):
        raise IdentifierRefusal(
            "Refused to save because supported identifier patterns were flagged. "
            "The check is assistive and not a guarantee of anonymisation."
        )


def check_record_identifiers(record: dict) -> None:
    """Scan all content except strictly validated structured dates."""
    validate_record(record)
    content = deepcopy(record)
    content["created"] = "structured date"
    for point in content["weekly_counts"]:
        point["week"] = "structured date"
    for key in ("reeaudit_date", "reaudit_date"):
        if content["audit"].get(key) is not None:
            content["audit"][key] = "structured date"
    check_identifiers(json.dumps(content, ensure_ascii=False, allow_nan=False))


def count_analysis(record: dict) -> list[str]:
    points = sorted(record["weekly_counts"], key=lambda point: point["week"])
    return analyse_series(
        [point["numerator"] / point["denominator"] for point in points],
        [point["week"] for point in points],
    )


def next_step(record: dict) -> tuple[str, str]:
    """Return one action and its reason, without classifying the project route."""
    validate_record(record)
    if record["route"] is None:
        return (
            "Confirm with your local QI/audit/governance team whether this is audit, service evaluation, QI or research; then set it.",
            "The project route has not been confirmed by the doctor.",
        )
    if not record["aim"].strip():
        return "Write a SMART aim with set-aim.", "The record has no aim to guide the work."
    for kind in KINDS:
        if not any(measure["kind"] == kind for measure in record["measures"]):
            return f"Add a {kind} measure with add-measure.", f"The {kind} measure is missing."
    for measure in record["measures"]:
        if not measure["definition"].strip():
            return f"Define the measure '{measure['name']}' using add-measure with the same name and kind.", "A repeatable measure needs an operational definition."
    if record["route"] == "research":
        return "Agree the research protocol and approvals with your local research team.", "The confirmed route is research and needs its own local oversight."
    stage = record["stage"]
    if record["route"] == "audit" or stage == "audit":
        for key in ("standard", "source", "sample_rules", "baseline_compliance", "reeaudit_date"):
            if record["audit"].get(key) in (None, ""):
                return f"Set the audit {key.replace('_', ' ')} in project.json.", "The audit needs a standard, source, sampling rules, baseline and a re-audit date."
        if stage != "write-up":
            return "Carry out the re-audit against the same standard and sampling rules.", "The audit baseline and re-audit date are recorded."
    elif stage in ("start", "test"):
        if not record["pdsa_cycles"]:
            return "Open a small PDSA cycle with add-pdsa and a prediction.", "A prediction makes the planned test assessable."
        for cycle in record["pdsa_cycles"]:
            if cycle["decision"] == "open":
                return f"Record PDSA {cycle['id']}'s result against its prediction and choose adopt, adapt or abandon with close-pdsa.", "The test is still open."
        return "Set the stage to measure and collect weekly numerator and denominator counts.", "The recorded PDSA tests have results and decisions."
    if stage == "measure":
        analysis = count_analysis(record)
        if analysis[0].startswith("too few"):
            return "Keep collecting weekly numerator and denominator counts with add-counts.", analysis[0]
        signals = [line for line in analysis if "signal:" in line]
        if signals:
            return "Review the named run-chart signal alongside the changes tested.", " ".join(signals) + " " + RUN_CHART_CAUTION
        return "Keep collecting weekly counts and review the next small test.", "No Shift or Trend signal found. " + RUN_CHART_CAUTION
    return "Write up the aim, methods, results, limitations and agreed next action.", "The project is at the write-up stage. " + RUN_CHART_CAUTION
