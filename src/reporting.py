# src/reporting.py
# Handles formatting and outputting the processed data and insights.

import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, Iterable, List, Optional

import config
from src import data_processor


ISSUE_METRIC_FIELDNAMES = [
    "key",
    "summary",
    "issue_type",
    "status",
    "project_key",
    "created",
    "resolutiondate",
    "cycle_time",
    "cycle_time_unit",
    "lead_time",
    "lead_time_unit",
    "data_quality_warning_count",
    "data_quality_warning_codes",
]


def _nested_name(value: Any) -> Optional[str]:
    """Extracts a display name from Jira nested objects when available."""
    if isinstance(value, dict):
        return value.get("name")
    if value is None:
        return None
    return str(value)


def _project_key(value: Any) -> Optional[str]:
    """Extracts a project key from Jira nested project data when available."""
    if isinstance(value, dict):
        return value.get("key") or value.get("name")
    if value is None:
        return None
    return str(value)


def build_issue_metric_rows(issues_data: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Converts processed Jira issue dictionaries into stable, export-friendly rows.

    Args:
        issues_data: Processed issue dictionaries, typically returned by
            data_processor.process_issues_for_metrics.

    Returns:
        A list of dictionaries using ISSUE_METRIC_FIELDNAMES.
    """
    rows: List[Dict[str, Any]] = []

    for issue in issues_data:
        fields = issue.get("fields", {}) or {}
        rows.append({
            "key": issue.get("key"),
            "summary": fields.get("summary"),
            "issue_type": _nested_name(fields.get("issuetype")),
            "status": _nested_name(fields.get("status")),
            "project_key": _project_key(fields.get("project")),
            "created": fields.get("created"),
            "resolutiondate": fields.get("resolutiondate"),
            "cycle_time": issue.get("cycle_time"),
            "cycle_time_unit": issue.get("cycle_time_unit"),
            "lead_time": issue.get("lead_time"),
            "lead_time_unit": issue.get("lead_time_unit"),
            "data_quality_warning_count": len(issue.get("data_quality_warnings", []) or []),
            "data_quality_warning_codes": ";".join(
                warning.get("code", "UNKNOWN_WARNING")
                for warning in issue.get("data_quality_warnings", []) or []
            ),
        })

    return rows


def _numeric_values(issues_data: Iterable[Dict[str, Any]], metric_name: str) -> List[float]:
    values: List[float] = []
    for issue in issues_data:
        value = issue.get(metric_name)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def _format_average(values: List[float]) -> str:
    if not values:
        return "N/A"
    return f"{mean(values):.2f}"


def _format_metric_value(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}"


def _completion_date(issue: Dict[str, Any]) -> Optional[Any]:
    throughput_done_statuses = getattr(config, "THROUGHPUT_DONE_STATUSES", None)
    if not isinstance(throughput_done_statuses, list):
        throughput_done_statuses = None
    return data_processor.get_completion_date(issue, throughput_done_statuses)


def _item_label(item: Dict[str, Any]) -> str:
    summary = item.get("summary")
    if summary:
        return f"{item.get('key')}: {summary}"
    return str(item.get("key"))


def _slowest_items(
    issues_data: Iterable[Dict[str, Any]],
    metric_name: str,
    limit: int,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []

    for issue in issues_data:
        value = issue.get(metric_name)
        if isinstance(value, (int, float)):
            items.append({
                "key": issue.get("key"),
                "summary": (issue.get("fields") or {}).get("summary"),
                "metric": metric_name,
                "value": float(value),
                "unit": issue.get(f"{metric_name}_unit"),
            })

    items.sort(key=lambda item: (-item["value"], item["key"] or ""))
    return items[:max(limit, 0)]


def _build_data_quality_observations(
    issues_data: List[Dict[str, Any]],
    cycle_times: List[float],
    lead_times: List[float],
    completed_count: int,
) -> List[str]:
    structured_observations = _structured_warning_observations(issues_data)
    if structured_observations:
        return structured_observations

    observations: List[str] = []
    issue_count = len(issues_data)
    missing_cycle_count = issue_count - len(cycle_times)
    missing_lead_count = issue_count - len(lead_times)
    missing_resolution_count = sum(
        1
        for issue in issues_data
        if ((issue.get("fields") or {}).get("resolutiondate") is None)
    )

    if issue_count == 0:
        observations.append("No issues were available for analysis.")
        return observations
    if completed_count == 0:
        observations.append(
            "No completed issues were detected; flow metrics may reflect active work only."
        )
    if missing_cycle_count:
        observations.append(
            f"{missing_cycle_count} issue(s) are missing cycle time; "
            "check status transition history and cycle status mapping."
        )
    if missing_lead_count:
        observations.append(
            f"{missing_lead_count} issue(s) are missing lead time; "
            "check created and resolution date fields."
        )
    if missing_resolution_count:
        observations.append(
            f"{missing_resolution_count} issue(s) do not have a resolution date."
        )
    if not observations:
        observations.append("No obvious data-quality gaps detected in processed metrics.")

    return observations


def _structured_warning_observations(
    issues_data: Iterable[Dict[str, Any]],
) -> List[str]:
    warning_counts: Dict[str, Dict[str, Any]] = {}

    for issue in issues_data:
        for warning in issue.get("data_quality_warnings", []) or []:
            code = warning.get("code", "UNKNOWN_WARNING")
            if code not in warning_counts:
                warning_counts[code] = {
                    "count": 0,
                    "message": warning.get("message", "Data quality warning."),
                }
            warning_counts[code]["count"] += 1

    observations: List[str] = []
    for code in sorted(warning_counts):
        warning_info = warning_counts[code]
        observations.append(
            f"{warning_info['count']} issue(s): {warning_info['message']}"
        )

    return observations


def build_insight_summary(
    issues_data: Iterable[Dict[str, Any]],
    throughput_period_start: Optional[Any] = None,
    throughput_period_end: Optional[Any] = None,
    slowest_item_limit: int = 3,
) -> Dict[str, Any]:
    """
    Builds a Scrum Master-oriented summary from processed issue metrics.

    Args:
        issues_data: Processed issue dictionaries.
        throughput_period_start: Optional inclusive start datetime for throughput.
        throughput_period_end: Optional exclusive end datetime for throughput.
        slowest_item_limit: Maximum number of slowest cycle-time items to include.

    Returns:
        A deterministic dictionary with summary metrics, bottleneck candidates,
        and data-quality observations.
    """
    issues = list(issues_data)
    cycle_times = _numeric_values(issues, "cycle_time")
    lead_times = _numeric_values(issues, "lead_time")
    completed_count = sum(1 for issue in issues if _completion_date(issue) is not None)
    wip_snapshot = data_processor.calculate_wip_snapshot(issues)

    throughput = None
    throughput_period = None
    if throughput_period_start is not None and throughput_period_end is not None:
        throughput = data_processor.calculate_throughput_for_period(
            issues,
            throughput_period_start,
            throughput_period_end,
        )
        throughput_period = {
            "start": throughput_period_start,
            "end": throughput_period_end,
        }

    return {
        "issue_count": len(issues),
        "completed_count": completed_count,
        "cycle_time": {
            "average": mean(cycle_times) if cycle_times else None,
            "median": median(cycle_times) if cycle_times else None,
            "unit": _first_metric_unit(issues, "cycle_time_unit"),
            "value_count": len(cycle_times),
        },
        "lead_time": {
            "average": mean(lead_times) if lead_times else None,
            "median": median(lead_times) if lead_times else None,
            "unit": _first_metric_unit(issues, "lead_time_unit"),
            "value_count": len(lead_times),
        },
        "throughput": throughput,
        "throughput_period": throughput_period,
        "wip": wip_snapshot,
        "slowest_items": _slowest_items(issues, "cycle_time", slowest_item_limit),
        "data_quality_observations": _build_data_quality_observations(
            issues,
            cycle_times,
            lead_times,
            completed_count,
        ),
    }


def _first_metric_unit(
    issues_data: Iterable[Dict[str, Any]],
    unit_field_name: str,
) -> Optional[str]:
    for issue in issues_data:
        unit = issue.get(unit_field_name)
        if unit:
            return str(unit)
    return None


def format_insight_summary(summary: Dict[str, Any]) -> str:
    """
    Formats a structured insight summary as concise console text.

    Args:
        summary: Dictionary returned by build_insight_summary.

    Returns:
        Human-readable report text for Scrum Master review.
    """
    cycle = summary["cycle_time"]
    lead = summary["lead_time"]
    cycle_unit = cycle.get("unit") or "days"
    lead_unit = lead.get("unit") or "days"
    lines = [
        "Jira Insights Scrum Master Summary",
        f"Issues analyzed: {summary['issue_count']}",
        f"Completed issues: {summary['completed_count']}",
        f"WIP snapshot: {summary['wip']['count']} active issue(s)",
        (
            "Cycle time: "
            f"avg {_format_metric_value(cycle['average'])} {cycle_unit}, "
            f"median {_format_metric_value(cycle['median'])} {cycle_unit}"
        ),
        (
            "Lead time: "
            f"avg {_format_metric_value(lead['average'])} {lead_unit}, "
            f"median {_format_metric_value(lead['median'])} {lead_unit}"
        ),
    ]

    if summary.get("throughput") is not None:
        lines.append(f"Throughput in selected period: {summary['throughput']}")

    lines.append("Slowest cycle-time items:")
    if summary["slowest_items"]:
        for item in summary["slowest_items"]:
            unit = item.get("unit") or cycle_unit
            lines.append(
                f"- {_item_label(item)} ({item['value']:.2f} {unit})"
            )
    else:
        lines.append("- N/A")

    lines.append("Data quality observations:")
    for observation in summary["data_quality_observations"]:
        lines.append(f"- {observation}")

    return "\n".join(lines)


def print_insight_summary(
    issues_data: Iterable[Dict[str, Any]],
    throughput_period_start: Optional[Any] = None,
    throughput_period_end: Optional[Any] = None,
    slowest_item_limit: int = 3,
) -> None:
    """
    Prints a Scrum Master-oriented insight summary for processed issue metrics.
    """
    summary = build_insight_summary(
        issues_data,
        throughput_period_start=throughput_period_start,
        throughput_period_end=throughput_period_end,
        slowest_item_limit=slowest_item_limit,
    )
    print(format_insight_summary(summary))


def build_mvp_report(
    issues_data: Iterable[Dict[str, Any]],
    throughput_period_start: Optional[Any] = None,
    throughput_period_end: Optional[Any] = None,
    slowest_item_limit: int = 3,
) -> Dict[str, Any]:
    """
    Builds the stable MVP report payload for repeated Scrum Master review.

    Args:
        issues_data: Processed issue dictionaries.
        throughput_period_start: Optional inclusive start datetime for throughput.
        throughput_period_end: Optional exclusive end datetime for throughput.
        slowest_item_limit: Maximum number of bottleneck candidates to include.

    Returns:
        A dictionary containing summary, bottleneck, data-quality, and issue rows.
    """
    issues = list(issues_data)
    summary = build_insight_summary(
        issues,
        throughput_period_start=throughput_period_start,
        throughput_period_end=throughput_period_end,
        slowest_item_limit=slowest_item_limit,
    )

    return {
        "report_name": "Jira Insights MVP Report",
        "summary": summary,
        "bottleneck_candidates": summary["slowest_items"],
        "data_quality": {
            "observations": summary["data_quality_observations"],
            "warning_counts": _warning_counts_by_code(issues),
        },
        "issue_details": build_issue_metric_rows(issues),
    }


def _warning_counts_by_code(issues_data: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for issue in issues_data:
        for warning in issue.get("data_quality_warnings", []) or []:
            code = warning.get("code", "UNKNOWN_WARNING")
            counts[code] = counts.get(code, 0) + 1
    return dict(sorted(counts.items()))


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_safe(nested_value) for key, nested_value in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def format_mvp_report(report: Dict[str, Any]) -> str:
    """
    Formats the stable MVP report payload as console-readable text.
    """
    lines = [
        report["report_name"],
        "",
        format_insight_summary(report["summary"]),
    ]

    lines.append("")
    lines.append("Issue detail rows: " + str(len(report["issue_details"])))

    warning_counts = report["data_quality"]["warning_counts"]
    lines.append("Warning counts:")
    if warning_counts:
        for code, count in warning_counts.items():
            lines.append(f"- {code}: {count}")
    else:
        lines.append("- None")

    return "\n".join(lines)


def write_report_json(report: Dict[str, Any], output_path: str) -> Path:
    """
    Writes the MVP report payload to JSON.

    Args:
        report: Report dictionary from build_mvp_report.
        output_path: Destination JSON path.

    Returns:
        The path of the written JSON file.
    """
    json_path = Path(output_path)
    with json_path.open("w", encoding="utf-8") as json_file:
        json.dump(_json_safe(report), json_file, indent=2, sort_keys=True)
        json_file.write("\n")
    return json_path


def print_metric_summary(issues_data: Iterable[Dict[str, Any]]) -> None:
    """
    Prints a concise console summary of processed issue metrics.

    Args:
        issues_data: Processed issue dictionaries.
    """
    issues = list(issues_data)
    cycle_times = _numeric_values(issues, "cycle_time")
    lead_times = _numeric_values(issues, "lead_time")
    completed_count = sum(
        1
        for issue in issues
        if (issue.get("fields") or {}).get("resolutiondate") is not None
    )

    print("Jira Insights Metric Summary")
    print(f"Issues analyzed: {len(issues)}")
    print(f"Completed issues: {completed_count}")
    print(f"Average cycle time: {_format_average(cycle_times)}")
    print(f"Average lead time: {_format_average(lead_times)}")


def write_metrics_csv(
    issues_data: Iterable[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Path:
    """
    Writes processed issue metrics to a CSV file.

    Args:
        issues_data: Processed issue dictionaries.
        output_path: Optional CSV path. Defaults to config.DEFAULT_OUTPUT_FILENAME.

    Returns:
        The path of the written CSV file.
    """
    csv_path = Path(output_path or config.DEFAULT_OUTPUT_FILENAME)
    rows = build_issue_metric_rows(issues_data)

    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=ISSUE_METRIC_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return csv_path
