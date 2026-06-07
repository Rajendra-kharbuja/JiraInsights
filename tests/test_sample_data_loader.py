from datetime import datetime, timezone

import pytest

import config
from src import data_processor
from src.sample_data_loader import SampleDataError, load_sample_issues


@pytest.fixture
def demo_metric_config(monkeypatch):
    monkeypatch.setattr(config, "CYCLE_START_STATUSES", ["In Progress"])
    monkeypatch.setattr(config, "CYCLE_END_STATUSES", ["Done", "Released"])
    monkeypatch.setattr(config, "THROUGHPUT_DONE_STATUSES", ["Done", "Released"])


def test_load_sample_issues_uses_committed_demo_data():
    issues = load_sample_issues()

    assert len(issues) == 4
    assert issues[0]["key"] == "DEMO-1"
    assert "fields" in issues[0]
    assert "status_transitions" in issues[0]


def test_loaded_sample_issues_are_safe_to_mutate_between_calls():
    first_load = load_sample_issues()
    first_load[0]["key"] = "CHANGED"

    second_load = load_sample_issues()

    assert second_load[0]["key"] == "DEMO-1"


def test_sample_data_processes_cycle_time_lead_time_and_throughput(demo_metric_config):
    issues = load_sample_issues()

    processed = data_processor.process_issues_for_metrics(issues)
    throughput = data_processor.calculate_throughput_for_period(
        processed,
        datetime(2024, 3, 1, tzinfo=timezone.utc),
        datetime(2024, 3, 12, tzinfo=timezone.utc),
    )

    assert processed[0]["cycle_time"] == pytest.approx(2.25)
    assert processed[0]["lead_time"] == pytest.approx(5.2708333333)
    assert processed[1]["cycle_time"] == pytest.approx(2.15625)
    assert processed[1]["lead_time"] is None
    assert processed[2]["cycle_time"] is None
    assert processed[3]["cycle_time"] == pytest.approx(4.9583333333)
    assert throughput == 3


def test_load_sample_issues_accepts_custom_path(tmp_path):
    sample_file = tmp_path / "custom_issues.json"
    sample_file.write_text('[{"key": "CUSTOM-1", "fields": {}}]', encoding="utf-8")

    issues = load_sample_issues(str(sample_file))

    assert issues == [{"key": "CUSTOM-1", "fields": {}}]


def test_load_sample_issues_rejects_invalid_json(tmp_path):
    sample_file = tmp_path / "bad.json"
    sample_file.write_text("{not-json", encoding="utf-8")

    with pytest.raises(SampleDataError, match="not valid JSON"):
        load_sample_issues(str(sample_file))


def test_load_sample_issues_rejects_non_list_json(tmp_path):
    sample_file = tmp_path / "not-a-list.json"
    sample_file.write_text('{"key": "CUSTOM-1"}', encoding="utf-8")

    with pytest.raises(SampleDataError, match="must be a JSON list"):
        load_sample_issues(str(sample_file))


def test_load_sample_issues_rejects_issue_without_key(tmp_path):
    sample_file = tmp_path / "missing-key.json"
    sample_file.write_text('[{"fields": {}}]', encoding="utf-8")

    with pytest.raises(SampleDataError, match="missing required 'key'"):
        load_sample_issues(str(sample_file))
