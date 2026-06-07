"""Command-line entry point for Jira Insights offline analysis workflows."""

import argparse
import sys
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import config
from src.data_processor import process_issues_for_metrics
from src.reporting import (
    build_mvp_report,
    print_insight_summary,
    write_metrics_csv,
    write_report_json,
)
from src.sample_data_loader import SampleDataError, load_sample_issues


DEMO_PERIOD_START = datetime(2024, 3, 1, tzinfo=timezone.utc)
DEMO_PERIOD_END = datetime(2024, 3, 12, tzinfo=timezone.utc)
DEMO_CYCLE_START_STATUSES = ["In Progress"]
DEMO_CYCLE_END_STATUSES = ["Done", "Released"]
DEMO_THROUGHPUT_DONE_STATUSES = ["Done", "Released"]
DEMO_WIP_STATUSES = ["In Progress", "Code Review"]


def _configure_demo_workflow_statuses() -> None:
    config.CYCLE_START_STATUSES = DEMO_CYCLE_START_STATUSES
    config.CYCLE_END_STATUSES = DEMO_CYCLE_END_STATUSES
    config.THROUGHPUT_DONE_STATUSES = DEMO_THROUGHPUT_DONE_STATUSES
    config.WIP_STATUSES = DEMO_WIP_STATUSES


def _parse_cli_datetime(value: str) -> datetime:
    try:
        if len(value) == 10:
            return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"'{value}' must be an ISO date or datetime."
        ) from exc

    if parsed.tzinfo is None or parsed.tzinfo.utcoffset(parsed) is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _resolve_period(args: argparse.Namespace) -> Tuple[Optional[datetime], Optional[datetime]]:
    period_start = getattr(args, "period_start", None)
    period_end = getattr(args, "period_end", None)

    if (period_start is None) != (period_end is None):
        raise ValueError("--period-start and --period-end must be provided together.")
    if period_start is not None and period_end <= period_start:
        raise ValueError("--period-end must be after --period-start.")

    return period_start, period_end


def _write_optional_exports(
    args: argparse.Namespace,
    processed_issues: list,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
) -> None:
    if getattr(args, "csv_output", None):
        csv_path = write_metrics_csv(processed_issues, args.csv_output)
        print(f"CSV issue details written to: {csv_path}")

    if getattr(args, "json_output", None):
        report = build_mvp_report(
            processed_issues,
            throughput_period_start=period_start,
            throughput_period_end=period_end,
        )
        json_path = write_report_json(report, args.json_output)
        print(f"JSON MVP report written to: {json_path}")


def _run_demo(args: argparse.Namespace) -> int:
    _configure_demo_workflow_statuses()
    issues = load_sample_issues(args.sample_path)
    processed_issues = process_issues_for_metrics(issues)
    print_insight_summary(
        processed_issues,
        throughput_period_start=DEMO_PERIOD_START,
        throughput_period_end=DEMO_PERIOD_END,
    )
    _write_optional_exports(
        args,
        processed_issues,
        period_start=DEMO_PERIOD_START,
        period_end=DEMO_PERIOD_END,
    )
    return 0


def _run_analyze_file(args: argparse.Namespace) -> int:
    period_start, period_end = _resolve_period(args)
    issues = load_sample_issues(args.input_path)
    processed_issues = process_issues_for_metrics(issues)
    print_insight_summary(
        processed_issues,
        throughput_period_start=period_start,
        throughput_period_end=period_end,
    )
    _write_optional_exports(
        args,
        processed_issues,
        period_start=period_start,
        period_end=period_end,
    )
    return 0


def _add_export_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--csv-output",
        help="Optional path for exported issue-level CSV details.",
    )
    parser.add_argument(
        "--json-output",
        help="Optional path for exported MVP report JSON.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze Jira-like issue data and generate Scrum Master insights."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Run the offline demo analysis using committed sample data.",
    )
    demo_parser.add_argument(
        "--sample-path",
        help="Optional path to a Jira-like sample JSON file.",
    )
    _add_export_arguments(demo_parser)
    demo_parser.set_defaults(handler=_run_demo)

    analyze_parser = subparsers.add_parser(
        "analyze-file",
        help="Analyze a Jira-like issue JSON file without Jira credentials.",
    )
    analyze_parser.add_argument("input_path", help="Path to a Jira-like issue JSON file.")
    analyze_parser.add_argument(
        "--period-start",
        type=_parse_cli_datetime,
        help="Optional throughput period start as ISO date or datetime, inclusive.",
    )
    analyze_parser.add_argument(
        "--period-end",
        type=_parse_cli_datetime,
        help="Optional throughput period end as ISO date or datetime, exclusive.",
    )
    _add_export_arguments(analyze_parser)
    analyze_parser.set_defaults(handler=_run_analyze_file)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        return args.handler(args)
    except (SampleDataError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
