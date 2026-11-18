import csv

import pytest

from improvement_guru.charts import analyse_run_chart_csv


def test_run_chart_analysis_writes_annotated_csv(tmp_path):
    output_path = tmp_path / "ed_flow_run_chart.csv"

    result = analyse_run_chart_csv(
        "examples/synthetic_ed_flow_qip.csv",
        output_path,
        value_column="median_time_to_initial_assessment_minutes",
        date_column="week",
        baseline_points=4,
    )

    assert result.output_path == output_path
    assert result.row_count == 12
    assert result.baseline_median == 41.5
    assert result.shift_signals >= 1
    assert result.trend_signals >= 1

    with output_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["qip_baseline_median"] == "41.5"
    assert rows[-1]["qip_shift_signal"] == "yes"
    assert rows[-1]["qip_trend_signal"] == "yes"


def test_run_chart_rejects_missing_value_column(tmp_path):
    output_path = tmp_path / "missing.csv"

    try:
        analyse_run_chart_csv(
            "examples/synthetic_ed_flow_qip.csv",
            output_path,
            value_column="not_a_column",
        )
    except ValueError as exc:
        assert "value column not found" in str(exc)
    else:
        raise AssertionError("missing value column should raise ValueError")


def _write_csv(path, contents):
    path.write_text(contents, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("", "missing a header row"),
        ("value\n", "no data rows"),
        ("value,other\n1\n", "malformed CSV row 2: expected 2 fields, found 1"),
        ("value\n1,unexpected\n", "malformed CSV row 2: expected 1 fields, found 2"),
        ("value\n\n", "malformed CSV row 2"),
        ('value\n"unterminated\n', "malformed CSV row 2"),
    ],
)
def test_run_chart_rejects_missing_or_malformed_rows(tmp_path, contents, message):
    input_path = _write_csv(tmp_path / "input.csv", contents)

    with pytest.raises(ValueError, match=message):
        analyse_run_chart_csv(input_path, tmp_path / "output.csv", value_column="value")


@pytest.mark.parametrize(
    ("raw_value", "message"),
    [
        (" ", "blank at CSV row 2"),
        ("not-a-number", "non-numeric data at CSV row 2"),
        ("NaN", "non-finite number at CSV row 2"),
        ("inf", "non-finite number at CSV row 2"),
        ("-Infinity", "non-finite number at CSV row 2"),
    ],
)
def test_run_chart_rejects_invalid_values(tmp_path, raw_value, message):
    input_path = _write_csv(tmp_path / "input.csv", f"value\n{raw_value}\n")

    with pytest.raises(ValueError, match=message):
        analyse_run_chart_csv(input_path, tmp_path / "output.csv", value_column="value")


@pytest.mark.parametrize(
    ("header", "message"),
    [
        ("value, ", "blank header at column 2"),
        ("value,value", "duplicate header: value"),
        ("value,qip_index", "conflicts with generated output column: qip_index"),
    ],
)
def test_run_chart_rejects_invalid_headers(tmp_path, header, message):
    input_path = _write_csv(tmp_path / "input.csv", f"{header}\n1,2\n")

    with pytest.raises(ValueError, match=message):
        analyse_run_chart_csv(input_path, tmp_path / "output.csv", value_column="value")


def test_run_chart_refuses_to_overwrite_existing_output(tmp_path):
    input_path = _write_csv(tmp_path / "input.csv", "value\n1\n2\n")
    output_path = _write_csv(tmp_path / "output.csv", "keep me\n")

    with pytest.raises(FileExistsError, match="output file already exists"):
        analyse_run_chart_csv(input_path, output_path, value_column="value")

    assert output_path.read_text(encoding="utf-8") == "keep me\n"


@pytest.mark.parametrize("length, expected", [(5, False), (6, True)])
def test_project_shift_threshold(length, expected):
    from improvement_guru.charts import analyse_series

    values = [0] * length + [2] * length
    lines = analyse_series(values, [str(i) for i in range(len(values))])
    assert any("Shift signal:" in line for line in lines) is expected


def test_project_shift_skips_median_without_breaking_run():
    from improvement_guru.charts import analyse_series

    values = [0] * 6 + [1] + [2] * 6
    lines = analyse_series(values, [str(i) for i in range(len(values))])
    assert "Shift signal: 6 points above the median (weeks 7 to 12)" in lines
    values = [0, 0, 1, 0, 0, 1, 0, 0] + [2] * 6
    lines = analyse_series(values, [str(i) for i in range(len(values))])
    assert "Shift signal: 6 points below the median (weeks 0 to 7)" in lines


@pytest.mark.parametrize("length, expected", [(4, False), (5, True)])
@pytest.mark.parametrize("descending", [False, True])
def test_project_trend_threshold_and_equal_values(length, expected, descending):
    from improvement_guru.charts import analyse_series

    values = [0, 9] * 5 + [2] * 2 + list(range(3, length + 2))
    if descending:
        values = [-value for value in values]
    lines = analyse_series(values, [str(i) for i in range(len(values))])
    trends = [line for line in lines if "Trend signal:" in line]
    assert bool(trends) is expected
    if expected:
        assert f"going {'down' if descending else 'up'}" in trends[0]
        assert "weeks 10 to 15" in trends[0]


def test_project_ten_usable_points_gate_drops_median():
    from improvement_guru.charts import analyse_series

    values = list(range(9)) + [4] * 20
    assert analyse_series(values, [str(i) for i in range(len(values))]) == [
        "too few points (8 of at least 10) to call a signal"
    ]
    assert analyse_series([], []) == ["too few points (0 of at least 10) to call a signal"]


def test_legacy_csv_ties_still_reset_without_ten_point_gate(tmp_path):
    source = _write_csv(tmp_path / "ties.csv", "value\n0\n0\n1\n0\n0\n0\n")
    destination = tmp_path / "out.csv"
    result = analyse_run_chart_csv(source, destination, value_column="value", baseline_points=3, run_length=2)
    with destination.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert result.row_count == 6
    assert rows[0]["qip_side"] == "on_median"
    assert rows[1]["qip_run_length"] == "0"
    assert rows[1]["qip_trend_length"] == "1"
