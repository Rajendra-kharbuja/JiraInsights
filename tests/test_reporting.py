import csv
import json
from datetime import datetime, timezone

import config
from src import reporting


def _issue(
    key="TEST-1",
    summary="Build reporting",
    issue_type="Story",
    status="Done",
    project_key="TEST",
    created="2023-01-01T00:00:00Z",
    resolutiondate="2023-01-03T00:00:00Z",
    cycle_time=1.5,
    lead_time=2.0,
    status_transitions=None,
):
    return {
        "key": key,
        "fields": {
            "summary": summary,
            "issuetype": {"name": issue_type},
            "status": {"name": status},
            "project": {"key": project_key},
            "created": created,
            "resolutiondate": resolutiondate,
        },
        "cycle_time": cycle_time,
        "cycle_time_unit": "days" if cycle_time is not None else None,
        "lead_time": lead_time,
        "lead_time_unit": "days" if lead_time is not None else None,
        "status_transitions": status_transitions or [],
    }


def test_build_issue_metric_rows_flattens_processed_issue_data():
    rows = reporting.build_issue_metric_rows([_issue()])

    assert rows == [{
        "key": "TEST-1",
        "summary": "Build reporting",
        "issue_type": "Story",
        "status": "Done",
        "project_key": "TEST",
        "created": "2023-01-01T00:00:00Z",
        "resolutiondate": "2023-01-03T00:00:00Z",
        "cycle_time": 1.5,
        "cycle_time_unit": "days",
        "lead_time": 2.0,
        "lead_time_unit": "days",
        "data_quality_warning_count": 0,
        "data_quality_warning_codes": "",
    }]


def test_build_issue_metric_rows_handles_missing_optional_fields():
    rows = reporting.build_issue_metric_rows([{"key": "TEST-2"}])

    assert rows[0]["key"] == "TEST-2"
    assert rows[0]["summary"] is None
    assert rows[0]["issue_type"] is None
    assert rows[0]["status"] is None
    assert rows[0]["project_key"] is None
    assert rows[0]["cycle_time"] is None
    assert rows[0]["lead_time"] is None
    assert rows[0]["data_quality_warning_count"] == 0
    assert rows[0]["data_quality_warning_codes"] == ""


def test_write_metrics_csv_writes_expected_headers_and_values(tmp_path):
    output_path = tmp_path / "metrics.csv"

    written_path = reporting.write_metrics_csv([_issue()], str(output_path))

    assert written_path == output_path
    with output_path.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == [{
        "key": "TEST-1",
        "summary": "Build reporting",
        "issue_type": "Story",
        "status": "Done",
        "project_key": "TEST",
        "created": "2023-01-01T00:00:00Z",
        "resolutiondate": "2023-01-03T00:00:00Z",
        "cycle_time": "1.5",
        "cycle_time_unit": "days",
        "lead_time": "2.0",
        "lead_time_unit": "days",
        "data_quality_warning_count": "0",
        "data_quality_warning_codes": "",
    }]


def test_build_issue_metric_rows_includes_data_quality_warning_codes():
    issue = _issue()
    issue["data_quality_warnings"] = [
        {
            "issue_key": "TEST-1",
            "code": "MISSING_CYCLE_END",
            "message": "No cycle end transition was found after cycle start.",
            "severity": "warning",
        },
        {
            "issue_key": "TEST-1",
            "code": "MISSING_RESOLUTION_DATE",
            "message": "Resolution date is missing.",
            "severity": "warning",
        },
    ]

    rows = reporting.build_issue_metric_rows([issue])

    assert rows[0]["data_quality_warning_count"] == 2
    assert rows[0]["data_quality_warning_codes"] == (
        "MISSING_CYCLE_END;MISSING_RESOLUTION_DATE"
    )


def test_print_metric_summary_handles_mixed_metric_availability(capsys):
    issues = [
        _issue(key="TEST-1", cycle_time=1.0, lead_time=3.0),
        _issue(
            key="TEST-2",
            resolutiondate=None,
            cycle_time=None,
            lead_time=None,
        ),
        _issue(key="TEST-3", cycle_time=3.0, lead_time=5.0),
    ]

    reporting.print_metric_summary(issues)

    output = capsys.readouterr().out
    assert "Jira Insights Metric Summary" in output
    assert "Issues analyzed: 3" in output
    assert "Completed issues: 2" in output
    assert "Average cycle time: 2.00" in output
    assert "Average lead time: 4.00" in output


def test_build_insight_summary_calculates_core_scrum_master_metrics(monkeypatch):
    monkeypatch.setattr(config, "WIP_STATUSES", ["In Progress"])
    issues = [
        _issue(key="TEST-1", summary="Fast item", cycle_time=1.0, lead_time=3.0),
        _issue(
            key="TEST-2",
            summary="Slow item",
            status="In Progress",
            cycle_time=5.0,
            lead_time=7.0,
        ),
        _issue(key="TEST-3", summary="Middle item", cycle_time=3.0, lead_time=5.0),
    ]

    summary = reporting.build_insight_summary(issues, slowest_item_limit=2)

    assert summary["issue_count"] == 3
    assert summary["completed_count"] == 3
    assert summary["cycle_time"]["average"] == 3.0
    assert summary["cycle_time"]["median"] == 3.0
    assert summary["lead_time"]["average"] == 5.0
    assert summary["lead_time"]["median"] == 5.0
    assert summary["wip"]["count"] == 1
    assert summary["wip"]["status_counts"] == {"In Progress": 1}
    assert summary["wip"]["issues"][0]["key"] == "TEST-2"
    assert [item["key"] for item in summary["slowest_items"]] == ["TEST-2", "TEST-3"]
    assert summary["data_quality_observations"] == [
        "No obvious data-quality gaps detected in processed metrics."
    ]


def test_build_insight_summary_handles_missing_metrics_and_no_completed_issues():
    issues = [
        _issue(
            key="TEST-1",
            resolutiondate=None,
            cycle_time=None,
            lead_time=None,
        ),
        _issue(
            key="TEST-2",
            resolutiondate=None,
            cycle_time=None,
            lead_time=None,
        ),
    ]

    summary = reporting.build_insight_summary(issues)

    assert summary["completed_count"] == 0
    assert summary["cycle_time"]["average"] is None
    assert summary["cycle_time"]["median"] is None
    assert summary["lead_time"]["average"] is None
    assert summary["lead_time"]["median"] is None
    assert summary["slowest_items"] == []
    assert (
        "No completed issues were detected; flow metrics may reflect active work only."
        in summary["data_quality_observations"]
    )
    assert (
        "2 issue(s) are missing cycle time; check status transition history and cycle status mapping."
        in summary["data_quality_observations"]
    )


def test_build_insight_summary_groups_structured_data_quality_warnings():
    issues = [
        {
            **_issue(key="TEST-1", resolutiondate=None),
            "data_quality_warnings": [{
                "issue_key": "TEST-1",
                "code": "MISSING_RESOLUTION_DATE",
                "message": "Resolution date is missing; lead time and completion detection may be limited.",
                "severity": "warning",
            }],
        },
        {
            **_issue(key="TEST-2", resolutiondate=None),
            "data_quality_warnings": [{
                "issue_key": "TEST-2",
                "code": "MISSING_RESOLUTION_DATE",
                "message": "Resolution date is missing; lead time and completion detection may be limited.",
                "severity": "warning",
            }],
        },
    ]

    summary = reporting.build_insight_summary(issues)

    assert summary["data_quality_observations"] == [
        "2 issue(s): Resolution date is missing; lead time and completion detection may be limited."
    ]


def test_build_insight_summary_uses_throughput_period(monkeypatch):
    monkeypatch.setattr(config, "THROUGHPUT_DONE_STATUSES", ["Done"])
    issues = [
        _issue(key="TEST-1", resolutiondate="2024-03-03T00:00:00Z"),
        _issue(key="TEST-2", resolutiondate="2024-03-10T00:00:00Z"),
        _issue(
            key="TEST-3",
            resolutiondate=None,
            status_transitions=[
                {
                    "timestamp": "2024-03-04T00:00:00Z",
                    "from_status": "In Progress",
                    "to_status": "Done",
                }
            ],
        ),
    ]

    summary = reporting.build_insight_summary(
        issues,
        throughput_period_start=datetime(2024, 3, 1, tzinfo=timezone.utc),
        throughput_period_end=datetime(2024, 3, 8, tzinfo=timezone.utc),
    )

    assert summary["completed_count"] == 3
    assert summary["throughput"] == 2


def test_format_insight_summary_is_deterministic_and_actionable():
    summary = {
        "issue_count": 2,
        "completed_count": 1,
        "cycle_time": {
            "average": 4.25,
            "median": 4.25,
            "unit": "days",
            "value_count": 2,
        },
        "lead_time": {
            "average": None,
            "median": None,
            "unit": None,
            "value_count": 0,
        },
        "throughput": 1,
        "throughput_period": None,
        "wip": {
            "count": 1,
            "statuses": ["In Progress"],
            "issues": [{
                "key": "TEST-2",
                "summary": "Review pull request",
                "status": "In Progress",
            }],
            "status_counts": {"In Progress": 1},
        },
        "slowest_items": [{
            "key": "TEST-9",
            "summary": "Investigate blocker",
            "metric": "cycle_time",
            "value": 8.5,
            "unit": "days",
        }],
        "data_quality_observations": [
            "1 issue(s) are missing lead time; check created and resolution date fields."
        ],
    }

    assert reporting.format_insight_summary(summary) == "\n".join([
        "Jira Insights Scrum Master Summary",
        "Issues analyzed: 2",
        "Completed issues: 1",
        "WIP snapshot: 1 active issue(s)",
        "Cycle time: avg 4.25 days, median 4.25 days",
        "Lead time: avg N/A days, median N/A days",
        "Throughput in selected period: 1",
        "Slowest cycle-time items:",
        "- TEST-9: Investigate blocker (8.50 days)",
        "Data quality observations:",
        "- 1 issue(s) are missing lead time; check created and resolution date fields.",
    ])


def test_build_mvp_report_combines_summary_quality_and_issue_details(monkeypatch):
    monkeypatch.setattr(config, "WIP_STATUSES", ["In Progress"])
    issue = _issue(key="TEST-1", summary="Report-ready item")
    issue["data_quality_warnings"] = [{
        "issue_key": "TEST-1",
        "code": "MISSING_CYCLE_END",
        "message": "No cycle end transition was found after cycle start; cycle time is incomplete.",
        "severity": "warning",
    }]

    report = reporting.build_mvp_report(
        [issue],
        throughput_period_start=datetime(2023, 1, 1, tzinfo=timezone.utc),
        throughput_period_end=datetime(2023, 1, 10, tzinfo=timezone.utc),
    )

    assert report["report_name"] == "Jira Insights MVP Report"
    assert report["summary"]["issue_count"] == 1
    assert "wip" in report["summary"]
    assert report["bottleneck_candidates"][0]["key"] == "TEST-1"
    assert report["data_quality"]["warning_counts"] == {"MISSING_CYCLE_END": 1}
    assert report["issue_details"][0]["data_quality_warning_count"] == 1


def test_format_mvp_report_includes_summary_and_warning_counts():
    report = {
        "report_name": "Jira Insights MVP Report",
        "summary": {
            "issue_count": 1,
            "completed_count": 1,
            "cycle_time": {
                "average": 2.0,
                "median": 2.0,
                "unit": "days",
                "value_count": 1,
            },
            "lead_time": {
                "average": 3.0,
                "median": 3.0,
                "unit": "days",
                "value_count": 1,
            },
            "throughput": None,
            "throughput_period": None,
            "wip": {
                "count": 0,
                "statuses": [],
                "issues": [],
                "status_counts": {},
            },
            "slowest_items": [],
            "data_quality_observations": ["No obvious data-quality gaps detected."],
        },
        "bottleneck_candidates": [],
        "data_quality": {"observations": [], "warning_counts": {"WARN": 2}},
        "issue_details": [{"key": "TEST-1"}],
    }

    output = reporting.format_mvp_report(report)

    assert "Jira Insights MVP Report" in output
    assert "Jira Insights Scrum Master Summary" in output
    assert "Issue detail rows: 1" in output
    assert "- WARN: 2" in output


def test_write_report_json_writes_json_safe_report(tmp_path):
    output_path = tmp_path / "report.json"
    report = {
        "report_name": "Jira Insights MVP Report",
        "summary": {
            "throughput_period": {
                "start": datetime(2024, 3, 1, tzinfo=timezone.utc),
                "end": datetime(2024, 3, 12, tzinfo=timezone.utc),
            }
        },
    }

    written_path = reporting.write_report_json(report, str(output_path))

    assert written_path == output_path
    with output_path.open(encoding="utf-8") as report_file:
        written_report = json.load(report_file)
    assert written_report["summary"]["throughput_period"]["start"] == (
        "2024-03-01T00:00:00+00:00"
    )
