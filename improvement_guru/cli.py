"""Improvement Guru command line interface."""

from __future__ import annotations

import argparse
from contextlib import suppress
from importlib import metadata
from pathlib import Path
import sys
import tomllib

from improvement_guru.charts import analyse_run_chart_csv
from improvement_guru.deid import redact_file, scan_file
from improvement_guru.paths import SOURCE_ROOT
from improvement_guru.scaffold import create_project
from improvement_guru.sources import format_profile, list_profiles, load_profile


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "new":
            return _run_new(args.project_name, args.profile)
        if args.command == "deid" and args.deid_command == "scan":
            return _run_scan(args.path)
        if args.command == "deid" and args.deid_command == "redact":
            return _run_redact(args.input_path, args.output_path)
        if args.command == "sources" and args.sources_command == "list":
            return _run_sources_list()
        if args.command == "sources" and args.sources_command == "show":
            return _run_sources_show(args.profile)
        if args.command == "charts" and args.charts_command == "run-chart":
            return _run_run_chart(
                args.input_path,
                args.output_path,
                args.value_column,
                args.date_column,
                args.baseline_points,
                args.run_length,
                args.trend_length,
            )
    except (OSError, ValueError) as exc:
        bundled_error = getattr(exc, "_bundled_resource_error", None)
        if bundled_error is not None:
            return _error(bundled_error)
        if args.command == "new":
            target = Path(args.project_name)
            if isinstance(exc, FileNotFoundError) and exc.filename == str(target):
                return _error(f"parent folder does not exist: {target.parent}")
            return _error(exc)
        raise

    getattr(args, "group_parser", parser).print_help(sys.stderr)
    return 2


class _VersionAction(argparse.Action):
    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: object,
        option_string: str | None = None,
    ) -> None:
        try:
            try:
                package_version = metadata.version("improvement-guru")
            except metadata.PackageNotFoundError:
                with (SOURCE_ROOT / "pyproject.toml").open("rb") as handle:
                    project = tomllib.load(handle).get("project", {})
                package_version = (
                    project.get("version") if project.get("name") == "improvement-guru" else None
                )
        except Exception:
            package_version = None
        if (
            not isinstance(package_version, str)
            or not package_version.strip()
            or package_version.splitlines() != [package_version]
        ):
            parser.exit(_error("could not determine the improvement-guru version"))
        print(f"{parser.prog} {package_version}")
        parser.exit()


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="improvement-guru",
        description="Public-safe QIP scaffold and deterministic assistive de-id helper.",
    )
    parser.add_argument(
        "--version", action=_VersionAction, nargs=0,
        help="show the program's version number and exit",
    )
    subparsers = parser.add_subparsers(dest="command")

    new_parser = subparsers.add_parser("new", help="create a new QIP project scaffold")
    new_parser.add_argument("project_name", help="folder name for the project scaffold")
    new_parser.add_argument(
        "--profile",
        default="global",
        help="source profile to attach to the scaffold, such as global, uk, us, canada, or australia",
    )

    deid_parser = subparsers.add_parser("deid", help="scan or redact supported identifiers")
    deid_parser.set_defaults(group_parser=deid_parser)
    deid_subparsers = deid_parser.add_subparsers(dest="deid_command")

    scan_parser = deid_subparsers.add_parser("scan", help="scan a UTF-8 CSV or text file")
    scan_parser.add_argument("path", help="input .csv or .txt file")

    redact_parser = deid_subparsers.add_parser("redact", help="write a redacted copy of a file")
    redact_parser.add_argument("input_path", help="input .csv or .txt file")
    redact_parser.add_argument("--out", required=True, dest="output_path", help="new output file path")

    sources_parser = subparsers.add_parser("sources", help="list or show source profiles")
    sources_parser.set_defaults(group_parser=sources_parser)
    sources_subparsers = sources_parser.add_subparsers(dest="sources_command")

    sources_subparsers.add_parser("list", help="list available source profiles")
    show_parser = sources_subparsers.add_parser("show", help="show one source profile")
    show_parser.add_argument("profile", help="profile id, such as global, uk, us, canada, or australia")

    charts_parser = subparsers.add_parser("charts", help="analyse QIP measurement CSV files")
    charts_parser.set_defaults(group_parser=charts_parser)
    charts_subparsers = charts_parser.add_subparsers(dest="charts_command")
    run_chart_parser = charts_subparsers.add_parser("run-chart", help="write annotated run-chart CSV output")
    run_chart_parser.add_argument("input_path", help="input CSV with one measure column")
    run_chart_parser.add_argument("--out", required=True, dest="output_path", help="new annotated output CSV path")
    run_chart_parser.add_argument("--value-column", required=True, help="numeric measure column to analyse")
    run_chart_parser.add_argument("--date-column", help="optional date/week column for readability")
    run_chart_parser.add_argument("--baseline-points", type=int, help="use the first N rows to calculate the median")
    run_chart_parser.add_argument(
        "--run-length", type=int, default=6,
        help="points on one side of median for shift signal (default: %(default)s)",
    )
    run_chart_parser.add_argument(
        "--trend-length", type=int, default=5,
        help="consecutive increasing/decreasing points for trend signal (default: %(default)s)",
    )

    return parser


def _run_new(project_name: str, profile: str) -> int:
    if not project_name:
        return _error("project name is empty")
    target = Path(project_name)
    created = create_project(target, target.name, profile_id=profile)
    for path in created:
        print(path)
    if sys.stdout.isatty() and sys.stderr.isatty():
        normalised_profile = profile.lower().strip()
        print(
            f"Created {len(created)} files in {target} (profile: {normalised_profile}).\n"
            "Next:\n"
            f"1. Open {target / 'charter.md'} and write your aim.\n"
            f"2. Read {target / 'source-map.md'} for the sources behind this profile.\n"
            "3. Before collecting data, confirm your local governance route and review the "
            "registration, information-governance and de-identification checklists.\n"
            "Keep patient-identifiable data out of this toolkit.",
            file=sys.stderr,
        )
    return 0


def _run_scan(path: str) -> int:
    try:
        findings = scan_file(path)
    except (OSError, ValueError) as exc:
        return _deid_error(exc, path)
    for finding in findings:
        print(f"{finding.line}:{finding.column}\t{finding.finding_type}\t{finding.preview}")
    if not findings:
        print("No supported identifier patterns found.")
        return 0
    return 1


def _run_redact(input_path: str, output_path: str) -> int:
    try:
        destination = redact_file(input_path, output_path)
    except (OSError, ValueError) as exc:
        return _deid_error(exc, input_path)
    print(destination)
    return 0


def _deid_error(exc: OSError | ValueError, input_path: str) -> int:
    if isinstance(exc, UnicodeDecodeError):
        return _error(f"{input_path!r} is not valid UTF-8 text; save the file as CSV UTF-8 and try again")
    # On Windows, opening a directory for reading can report permission denied.
    if isinstance(exc, PermissionError) and exc.filename is not None:
        source = Path(input_path)
        with suppress(OSError):
            if source == Path(exc.filename) and source.is_dir():
                return _error(f"Is a directory: {input_path!r}")
    return _error(exc)


def _error(reason: str | OSError | ValueError) -> int:
    if isinstance(reason, OSError) and reason.strerror and reason.filename is not None:
        message = f"{reason.strerror}: {reason.filename!r}"
    else:
        message = str(reason)
    message = message.replace("\r", r"\r").replace("\n", r"\n")
    print(f"Error: {message}", file=sys.stderr)
    return 2


def _run_sources_list() -> int:
    try:
        profiles = list_profiles()
    except ValueError as exc:
        if getattr(exc, "_bundled_resource_error", None) is not None:
            raise
        return _error(exc)
    for profile in profiles:
        print(f"{profile['id']}\t{profile['name']}")
    return 0


def _run_sources_show(profile: str) -> int:
    try:
        source = load_profile(profile)
    except ValueError as exc:
        if getattr(exc, "_bundled_resource_error", None) is not None:
            raise
        return _error(exc)
    print(format_profile(source))
    return 0


def _run_run_chart(
    input_path: str,
    output_path: str,
    value_column: str,
    date_column: str | None,
    baseline_points: int | None,
    run_length: int,
    trend_length: int,
) -> int:
    try:
        result = analyse_run_chart_csv(
            input_path,
            output_path,
            value_column=value_column,
            date_column=date_column,
            baseline_points=baseline_points,
            run_length=run_length,
            trend_length=trend_length,
        )
    except (FileExistsError, ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(
        f"{result.output_path}\trows={result.row_count}\tmedian={result.baseline_median:g}"
        f"\tshifts={result.shift_signals}\ttrends={result.trend_signals}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
