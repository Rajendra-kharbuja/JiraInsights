import csv
import json

import pytest

import main as cli


def test_cli_help_lists_available_commands(capsys):
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "demo" in output
    assert "analyze-file" in output


def test_demo_command_prints_scrum_master_summary(capsys):
    exit_code = cli.main(["demo"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Jira Insights Scrum Master Summary" in output
    assert "Issues analyzed: 4" in output
    assert "Completed issues: 3" in output
    assert "Throughput in selected period: 3" in output
    assert "DEMO-4: Add product analytics event validation" in output


def test_demo_command_output_does_not_include_diagnostic_noise(capsys):
    exit_code = cli.main(["demo"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "INFO [config.py]" not in captured.out
    assert "DEBUG" not in captured.out
    assert "src.data_processor" not in captured.err


def test_demo_command_writes_optional_exports(tmp_path, capsys):
    csv_output = tmp_path / "demo_details.csv"
    json_output = tmp_path / "demo_report.json"

    exit_code = cli.main([
        "demo",
        "--csv-output",
        str(csv_output),
        "--json-output",
        str(json_output),
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "CSV issue details written to:" in output
    assert "JSON MVP report written to:" in output

    with csv_output.open(newline="", encoding="utf-8") as csv_file:
        csv_rows = list(csv.DictReader(csv_file))
    assert csv_rows[0]["key"] == "DEMO-1"
    assert "data_quality_warning_count" in csv_rows[0]

    with json_output.open(encoding="utf-8") as json_file:
        report = json.load(json_file)
    assert report["report_name"] == "Jira Insights MVP Report"
    assert report["summary"]["issue_count"] == 4


def test_analyze_file_command_prints_summary_for_custom_file(tmp_path, capsys):
    sample_file = tmp_path / "issues.json"
    sample_file.write_text(
        """
        [
          {
            "key": "CUSTOM-1",
            "fields": {
              "summary": "Validate CLI file analysis",
              "created": "2024-03-01T00:00:00.000+0000",
              "resolutiondate": "2024-03-02T00:00:00.000+0000"
            },
            "cycle_time": 1.0,
            "cycle_time_unit": "days",
            "lead_time": 1.0,
            "lead_time_unit": "days"
          }
        ]
        """,
        encoding="utf-8",
    )

    exit_code = cli.main([
        "analyze-file",
        str(sample_file),
        "--period-start",
        "2024-03-01",
        "--period-end",
        "2024-03-03",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Issues analyzed: 1" in output
    assert "Completed issues: 1" in output
    assert "Throughput in selected period: 1" in output


def test_analyze_file_command_writes_json_export(tmp_path, capsys):
    sample_file = tmp_path / "issues.json"
    json_output = tmp_path / "report.json"
    sample_file.write_text('[{"key": "CUSTOM-1", "fields": {}}]', encoding="utf-8")

    exit_code = cli.main([
        "analyze-file",
        str(sample_file),
        "--json-output",
        str(json_output),
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "JSON MVP report written to:" in output
    with json_output.open(encoding="utf-8") as json_file:
        report = json.load(json_file)
    assert report["issue_details"][0]["key"] == "CUSTOM-1"


def test_analyze_file_command_reports_invalid_file(capsys):
    exit_code = cli.main(["analyze-file", "missing-file.json"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "Error: Sample data file not found:" in captured.err


def test_analyze_file_requires_complete_period(capsys):
    exit_code = cli.main([
        "analyze-file",
        "sample_data/demo_issues.json",
        "--period-start",
        "2024-03-01",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--period-start and --period-end must be provided together" in captured.err
