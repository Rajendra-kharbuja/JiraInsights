# tests/test_data_processor.py
import pytest
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Ensure project root is on path for `import config` and `from src import ...`
# conftest.py should handle this if pytest is run from root.
from src import data_processor 
import config # To mock its attributes for testing

# --- Helper to create mock transition data ---
def create_transition(timestamp_str: str, from_s: Optional[str], to_s: str) -> Dict[str, Any]:
    return {"timestamp": timestamp_str, "from_status": from_s, "to_status": to_s}

# --- Tests for _parse_iso_datetime ---
def test_parse_iso_datetime_valid_zulu():
    dt = data_processor._parse_iso_datetime("2023-01-15T10:30:00.123Z")
    assert dt is not None
    assert dt == datetime(2023, 1, 15, 10, 30, 0, 123000, tzinfo=timezone.utc)

def test_parse_iso_datetime_valid_offset():
    dt = data_processor._parse_iso_datetime("2023-01-15T10:30:00.000-05:00")
    assert dt is not None
    assert dt == datetime(2023, 1, 15, 15, 30, 0, 0, tzinfo=timezone.utc) # Converted to UTC

def test_parse_iso_datetime_valid_plus_0000():
    dt = data_processor._parse_iso_datetime("2023-01-15T10:30:00.000+0000")
    assert dt is not None
    assert dt == datetime(2023, 1, 15, 10, 30, 0, 0, tzinfo=timezone.utc)

def test_parse_iso_datetime_invalid_format(caplog):
    assert data_processor._parse_iso_datetime("invalid-date-string") is None
    assert "Error parsing timestamp string 'invalid-date-string'" in caplog.text

def test_parse_iso_datetime_none_input():
    assert data_processor._parse_iso_datetime(None) is None

# --- Tests for calculate_cycle_time ---
class TestCalculateCycleTime:
    start_statuses = ["In Progress", "Dev"]
    end_statuses = ["Resolved", "Closed"]

    def test_happy_path_simple(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-03T10:00:00Z", "In Progress", "Resolved"),
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "days")
        assert ct == pytest.approx(2.0)

    def test_no_start_status_found(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "Open"),
            create_transition("2023-01-03T10:00:00Z", "Open", "Resolved"), # End status, but no start
        ]
        assert data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses) is None

    def test_start_status_no_end_status_found(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-03T10:00:00Z", "In Progress", "Review"), # Not an end status
        ]
        assert data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses) is None
        
    def test_multiple_start_end_uses_first_valid_pair(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"), # First Start
            create_transition("2023-01-02T10:00:00Z", "In Progress", "Dev"),      # Still Start
            create_transition("2023-01-03T10:00:00Z", "Dev", "Resolved"),   # First End
            create_transition("2023-01-04T10:00:00Z", "Resolved", "In Progress"),# Re-enters Start
            create_transition("2023-01-05T10:00:00Z", "In Progress", "Closed"),  # Second End
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "days")
        # Expected: 2023-01-03 (Resolved) - 2023-01-01 (In Progress) = 2 days
        assert ct == pytest.approx(2.0)

    def test_end_status_before_start_status_chronologically(self):
        # This scenario relies on the input transitions being sorted.
        # If an end status appears before a start, it shouldn't be picked if no start was found yet.
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "Resolved"), # End before Start
            create_transition("2023-01-02T10:00:00Z", "Resolved", "In Progress"), # Start
            create_transition("2023-01-03T10:00:00Z", "In Progress", "Closed"), # End
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "days")
        # Expected: 2023-01-03 (Closed) - 2023-01-02 (In Progress) = 1 day
        assert ct == pytest.approx(1.0)

    def test_empty_transitions_list(self):
        assert data_processor.calculate_cycle_time([], self.start_statuses, self.end_statuses) is None

    def test_empty_start_statuses(self):
        transitions = [create_transition("2023-01-01T10:00:00Z", "Open", "In Progress")]
        assert data_processor.calculate_cycle_time(transitions, [], self.end_statuses) is None

    def test_empty_end_statuses(self):
        transitions = [create_transition("2023-01-01T10:00:00Z", "Open", "In Progress")]
        assert data_processor.calculate_cycle_time(transitions, self.start_statuses, []) is None

    def test_output_unit_hours(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-01T12:00:00Z", "In Progress", "Resolved"),
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "hours")
        assert ct == pytest.approx(2.0)

    def test_output_unit_minutes(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-01T10:05:00Z", "In Progress", "Resolved"),
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "minutes")
        assert ct == pytest.approx(5.0)
    
    def test_output_unit_seconds(self):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-01T10:00:30Z", "In Progress", "Resolved"),
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "seconds")
        assert ct == pytest.approx(30.0)

    def test_invalid_output_unit_defaults_to_days(self, caplog):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("2023-01-02T10:00:00Z", "In Progress", "Resolved"),
        ]
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "years")
        assert ct == pytest.approx(1.0) # 1 day
        assert "Invalid output_unit for cycle time: 'years'" in caplog.text
        
    def test_malformed_timestamp_in_transitions(self, caplog):
        transitions = [
            create_transition("2023-01-01T10:00:00Z", "Open", "In Progress"),
            create_transition("INVALID_TIMESTAMP", "In Progress", "Review"),
            create_transition("2023-01-03T10:00:00Z", "Review", "Resolved"),
        ]
        # Behavior depends on how _parse_iso_datetime handles it and if calculate_cycle_time skips.
        # Current _parse_iso_datetime returns None and logs error.
        # calculate_cycle_time should ideally still find the valid end if start was valid.
        ct = data_processor.calculate_cycle_time(transitions, self.start_statuses, self.end_statuses, "days")
        assert "Error parsing timestamp string 'INVALID_TIMESTAMP'" in caplog.text
        # It should still calculate based on valid start and valid subsequent end
        assert ct == pytest.approx(2.0) # 2023-01-03 minus 2023-01-01

# --- Tests for process_issues_for_metrics ---
@pytest.fixture
def mock_config_cycle_statuses(monkeypatch): # Removed self from fixture
    """ Mocks config.CYCLE_START_STATUSES and config.CYCLE_END_STATUSES """
    monkeypatch.setattr(config, "CYCLE_START_STATUSES", ["Dev Start"])
    monkeypatch.setattr(config, "CYCLE_END_STATUSES", ["Dev Done"])

def test_process_issues_adds_cycle_time(mock_config_cycle_statuses): # Removed self
    issues_data = [
        {"key": "TEST-1", "status_transitions": [
            create_transition("2023-01-01T00:00:00Z", "Open", "Dev Start"),
            create_transition("2023-01-02T00:00:00Z", "Dev Start", "Dev Done"),
        ]},
        {"key": "TEST-2", "status_transitions": [ # No valid cycle
            create_transition("2023-01-03T00:00:00Z", "Open", "Review"),
        ]}
    ]
    processed = data_processor.process_issues_for_metrics(issues_data, cycle_time_output_unit="days")
    
    assert len(processed) == 2
    assert processed[0]["key"] == "TEST-1"
    assert processed[0]["cycle_time"] == pytest.approx(1.0)
    assert processed[0]["cycle_time_unit"] == "days"

    assert processed[1]["key"] == "TEST-2"
    assert processed[1]["cycle_time"] is None
    assert processed[1]["cycle_time_unit"] is None


def test_process_issues_no_config_statuses(monkeypatch, caplog): # Removed self
    # Temporarily remove the attributes from the imported config module for this test
    if hasattr(config, 'CYCLE_START_STATUSES'):
        monkeypatch.delattr(config, 'CYCLE_START_STATUSES')
    if hasattr(config, 'CYCLE_END_STATUSES'):
        monkeypatch.delattr(config, 'CYCLE_END_STATUSES')
        
    issues_data = [{"key": "TEST-1", "status_transitions": []}]
    processed = data_processor.process_issues_for_metrics(issues_data)
    
    assert "CYCLE_START_STATUSES or CYCLE_END_STATUSES not found in config" in caplog.text
    assert processed[0]["cycle_time"] is None

def test_process_issues_empty_config_statuses(monkeypatch, caplog): # Removed self
    monkeypatch.setattr(config, "CYCLE_START_STATUSES", [])
    monkeypatch.setattr(config, "CYCLE_END_STATUSES", ["Done"]) # One is empty
        
    issues_data = [{"key": "TEST-1", "status_transitions": []}]
    processed = data_processor.process_issues_for_metrics(issues_data)
    
    assert "CYCLE_START_STATUSES or CYCLE_END_STATUSES are empty in config" in caplog.text
    assert processed[0]["cycle_time"] is None
# --- Tests for calculate_lead_time ---
class TestCalculateLeadTime:
    def test_happy_path_days(self):
        lt = data_processor.calculate_lead_time(
            "2023-01-01T10:00:00Z", 
            "2023-01-05T10:00:00Z", 
            "days"
        )
        assert lt == pytest.approx(4.0)

    def test_happy_path_hours(self):
        lt = data_processor.calculate_lead_time(
            "2023-01-01T10:00:00Z", 
            "2023-01-01T14:00:00Z", 
            "hours"
        )
        assert lt == pytest.approx(4.0)

    def test_happy_path_sub_day(self):
        lt = data_processor.calculate_lead_time(
            "2023-01-01T10:00:00Z", 
            "2023-01-01T10:30:00Z", 
            "days"
        )
        assert lt == pytest.approx(30.0 / (24 * 60)) # 0.5 hours / 24

    def test_missing_created_timestamp(self, caplog):
        lt = data_processor.calculate_lead_time(None, "2023-01-05T10:00:00Z")
        assert lt is None
        assert "Created timestamp is missing" in caplog.text

    def test_missing_resolved_timestamp(self, caplog):
        lt = data_processor.calculate_lead_time("2023-01-01T10:00:00Z", None)
        assert lt is None
        assert "Resolved timestamp is missing" in caplog.text

    def test_malformed_created_timestamp(self, caplog):
        lt = data_processor.calculate_lead_time("invalid-date", "2023-01-05T10:00:00Z")
        assert lt is None
        assert "Failed to parse created timestamp 'invalid-date'" in caplog.text

    def test_malformed_resolved_timestamp(self, caplog):
        lt = data_processor.calculate_lead_time("2023-01-01T10:00:00Z", "invalid-date")
        assert lt is None
        assert "Failed to parse resolved timestamp 'invalid-date'" in caplog.text

    def test_resolved_before_created(self, caplog):
        lt = data_processor.calculate_lead_time(
            "2023-01-05T10:00:00Z", 
            "2023-01-01T10:00:00Z"
        )
        assert lt is None
        assert "Resolved time" in caplog.text
        assert "is before created time" in caplog.text

    def test_invalid_output_unit_defaults_to_days(self, caplog):
        lt = data_processor.calculate_lead_time(
            "2023-01-01T10:00:00Z", 
            "2023-01-02T10:00:00Z", 
            "eons"
        )
        assert lt == pytest.approx(1.0) # 1 day
        assert "Invalid output_unit for lead time: 'eons'" in caplog.text

# --- Updated Tests for process_issues_for_metrics ---
# (We need to ensure the mock_config_cycle_statuses fixture is available or adapt)
# For simplicity, let's modify the existing test_process_issues_adds_cycle_time
# and add a new one specifically for lead time.

class TestProcessIssuesForMetrics: # Grouping tests for this function

    @pytest.fixture
    def mock_config_statuses(self, monkeypatch):
        """ Mocks config attributes for cycle time statuses. """
        monkeypatch.setattr(config, "CYCLE_START_STATUSES", ["Dev Start", "In Progress"])
        monkeypatch.setattr(config, "CYCLE_END_STATUSES", ["Dev Done", "Resolved"])
        # For lead time, no specific status config needed from config.py itself

    def test_process_issues_adds_cycle_and_lead_time(self, mock_config_statuses):
        issues_data = [
            { # Issue 1: Calculable Cycle Time and Lead Time
                "key": "TEST-1",
                "fields": {
                    "created": "2023-01-01T00:00:00Z",
                    "resolutiondate": "2023-01-03T00:00:00Z"
                },
                "status_transitions": [
                    create_transition("2023-01-01T12:00:00Z", "Open", "Dev Start"),
                    create_transition("2023-01-02T12:00:00Z", "Dev Start", "Dev Done"),
                ]
            },
            { # Issue 2: No valid cycle time, but calculable lead time
                "key": "TEST-2",
                "fields": {
                    "created": "2023-01-02T00:00:00Z",
                    "resolutiondate": "2023-01-04T00:00:00Z" 
                },
                "status_transitions": [
                    create_transition("2023-01-03T00:00:00Z", "Open", "Review"),
                ]
            },
            { # Issue 3: Valid cycle time, but no resolution date (no lead time)
                "key": "TEST-3",
                "fields": {
                    "created": "2023-01-03T00:00:00Z",
                    "resolutiondate": None # Not resolved
                },
                "status_transitions": [
                    create_transition("2023-01-03T10:00:00Z", "Backlog", "In Progress"),
                    create_transition("2023-01-04T10:00:00Z", "In Progress", "Resolved"),
                ]
            }
        ]
        
        # Use default output units ("days")
        processed = data_processor.process_issues_for_metrics(list(issues_data)) # Pass a copy
        
        assert len(processed) == 3
        
        # Issue 1
        assert processed[0]["key"] == "TEST-1"
        assert processed[0]["cycle_time"] == pytest.approx(1.0)
        assert processed[0]["cycle_time_unit"] == "days"
        assert processed[0]["lead_time"] == pytest.approx(2.0)
        assert processed[0]["lead_time_unit"] == "days"

        # Issue 2
        assert processed[1]["key"] == "TEST-2"
        assert processed[1]["cycle_time"] is None
        assert processed[1]["cycle_time_unit"] is None
        assert processed[1]["lead_time"] == pytest.approx(2.0)
        assert processed[1]["lead_time_unit"] == "days"

        # Issue 3
        assert processed[2]["key"] == "TEST-3"
        assert processed[2]["cycle_time"] == pytest.approx(1.0)
        assert processed[2]["cycle_time_unit"] == "days"
        assert processed[2]["lead_time"] is None
        assert processed[2]["lead_time_unit"] is None

    # Keep existing tests for process_issues_for_metrics regarding missing/empty cycle time config
    # (test_process_issues_no_config_statuses and test_process_issues_empty_config_statuses)
    # They will now also assign None to lead_time fields, which is fine.
    # We can add more specific tests for lead_time units if needed.

    def test_process_issues_no_config_statuses_still_adds_lead_time(self, monkeypatch, caplog):
        if hasattr(config, 'CYCLE_START_STATUSES'):
            monkeypatch.delattr(config, 'CYCLE_START_STATUSES', raising=False) # Use raising=False
        if hasattr(config, 'CYCLE_END_STATUSES'):
            monkeypatch.delattr(config, 'CYCLE_END_STATUSES', raising=False)
            
        issues_data = [{
            "key": "TEST-LT", 
            "fields": {"created": "2023-01-10T00:00:00Z", "resolutiondate": "2023-01-11T00:00:00Z"},
            "status_transitions": []
        }]
        processed = data_processor.process_issues_for_metrics(list(issues_data)) # Pass a copy
        
        assert "CYCLE_START_STATUSES or CYCLE_END_STATUSES not found in config" in caplog.text
        assert processed[0]["cycle_time"] is None
        assert processed[0]["lead_time"] == pytest.approx(1.0) # Lead time should still be calculated
        assert processed[0]["lead_time_unit"] == "days"

    def test_process_issues_lead_time_different_unit(self, mock_config_statuses):
        issues_data = [{
            "key": "TEST-UNIT",
            "fields": {"created": "2023-02-01T08:00:00Z", "resolutiondate": "2023-02-01T10:00:00Z"},
            "status_transitions": [] # No cycle time for simplicity here
        }]
        processed = data_processor.process_issues_for_metrics(
            list(issues_data), 
            lead_time_output_unit="hours"
        )
        assert processed[0]["lead_time"] == pytest.approx(2.0)
        assert processed[0]["lead_time_unit"] == "hours"
# --- Tests for get_completion_date ---
class TestGetCompletionDate:
    # Sample issue data structure for tests
    def _create_issue(self, key="T-1", created=None, resolutiondate=None, transitions=None, fields_override=None):
        issue = {"key": key, "fields": {}, "status_transitions": transitions or []}
        if created: issue["fields"]["created"] = created
        if resolutiondate: issue["fields"]["resolutiondate"] = resolutiondate
        if fields_override: issue["fields"].update(fields_override)
        return issue

    def test_from_resolutiondate(self):
        issue = self._create_issue(resolutiondate="2023-01-10T12:00:00Z")
        comp_date = data_processor.get_completion_date(issue)
        assert comp_date == datetime(2023, 1, 10, 12, 0, 0, tzinfo=timezone.utc)

    def test_from_status_transition(self):
        done_statuses = ["Done", "Closed"]
        transitions = [create_transition("2023-01-09T10:00:00Z", "Review", "Done")]
        issue = self._create_issue(transitions=transitions) # No resolutiondate
        comp_date = data_processor.get_completion_date(issue, done_statuses)
        assert comp_date == datetime(2023, 1, 9, 10, 0, 0, tzinfo=timezone.utc)

    def test_resolutiondate_precedence(self):
        # resolutiondate is earlier than a "Done" status transition
        done_statuses = ["Done"]
        transitions = [create_transition("2023-01-11T00:00:00Z", "Review", "Done")]
        issue = self._create_issue(resolutiondate="2023-01-10T18:00:00Z", transitions=transitions)
        comp_date = data_processor.get_completion_date(issue, done_statuses)
        assert comp_date == datetime(2023, 1, 10, 18, 0, 0, tzinfo=timezone.utc)

    def test_no_resolutiondate_no_valid_done_status_transition(self):
        done_statuses = ["Actually Done"]
        transitions = [create_transition("2023-01-09T10:00:00Z", "Review", "Almost Done")]
        issue = self._create_issue(transitions=transitions)
        assert data_processor.get_completion_date(issue, done_statuses) is None

    def test_malformed_resolutiondate_falls_back_to_status(self, caplog):
        done_statuses = ["Done"]
        transitions = [create_transition("2023-01-11T00:00:00Z", "Review", "Done")]
        issue = self._create_issue(resolutiondate="invalid-date", transitions=transitions)
        
        comp_date = data_processor.get_completion_date(issue, done_statuses)
        assert "Had resolutiondate 'invalid-date' but failed to parse" in caplog.text
        assert comp_date == datetime(2023, 1, 11, 0, 0, 0, tzinfo=timezone.utc)

    def test_empty_done_statuses_list_uses_resolutiondate_only(self):
        issue_with_resdate = self._create_issue(resolutiondate="2023-01-10T12:00:00Z")
        issue_no_resdate_with_done_transition = self._create_issue(
            transitions=[create_transition("2023-01-11T00:00:00Z", "Review", "Done")]
        )
        
        # Test with empty list
        comp_date1 = data_processor.get_completion_date(issue_with_resdate, [])
        assert comp_date1 == datetime(2023, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        comp_date2 = data_processor.get_completion_date(issue_no_resdate_with_done_transition, [])
        assert comp_date2 is None

        # Test with None
        comp_date3 = data_processor.get_completion_date(issue_with_resdate, None)
        assert comp_date3 == datetime(2023, 1, 10, 12, 0, 0, tzinfo=timezone.utc)
        comp_date4 = data_processor.get_completion_date(issue_no_resdate_with_done_transition, None)
        assert comp_date4 is None

    def test_done_status_transition_malformed_timestamp(self, caplog):
        done_statuses = ["Done"]
        transitions = [create_transition("bad-time", "Review", "Done")]
        issue = self._create_issue(transitions=transitions)
        assert data_processor.get_completion_date(issue, done_statuses) is None
        assert "timestamp 'bad-time' was unparseable" in caplog.text


# --- Tests for calculate_throughput_for_period ---
class TestCalculateThroughputForPeriod:
    def _create_issue_with_completion_date(self, key, completion_date_str, done_statuses_config=None):
        """Helper to create issue data where get_completion_date will return a specific date."""
        issue = {"key": key, "fields": {}, "status_transitions": []}
        # Simulate how get_completion_date would work
        if done_statuses_config and "status:" in completion_date_str: # e.g., "status:2023-01-05T00:00:00Z"
            status_time = completion_date_str.split("status:")[1]
            issue["status_transitions"].append(create_transition(status_time, "Prev", done_statuses_config[0]))
        elif completion_date_str:
            issue["fields"]["resolutiondate"] = completion_date_str
        return issue

    @pytest.fixture
    def mock_config_throughput_done(self, monkeypatch):
        monkeypatch.setattr(config, "THROUGHPUT_DONE_STATUSES", ["Resolved", "Shipped"])

    def test_no_issues_data(self):
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period([], start_dt, end_dt) == 0

    def test_one_issue_in_period_by_resolutiondate(self, mock_config_throughput_done):
        issues = [self._create_issue_with_completion_date("T1", "2023-01-05T12:00:00Z")]
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc) # End of Jan 7th
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 1
        
    def test_one_issue_in_period_by_status(self, mock_config_throughput_done):
        # Get the configured done statuses for the helper
        done_statuses = config.THROUGHPUT_DONE_STATUSES 
        issues = [self._create_issue_with_completion_date("T1", f"status:{'2023-01-05T12:00:00Z'}", done_statuses)]
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 1

    def test_multiple_issues_in_period(self, mock_config_throughput_done):
        done_statuses = config.THROUGHPUT_DONE_STATUSES
        issues = [
            self._create_issue_with_completion_date("T1", "2023-01-02T00:00:00Z"),
            self._create_issue_with_completion_date("T2", f"status:{'2023-01-04T00:00:00Z'}", done_statuses),
            self._create_issue_with_completion_date("T3", "2023-01-07T23:59:59Z"),
        ]
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 3

    def test_issue_completed_before_period(self, mock_config_throughput_done):
        issues = [self._create_issue_with_completion_date("T1", "2022-12-31T23:59:59Z")]
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 0

    def test_issue_completed_on_period_end_exclusive(self, mock_config_throughput_done):
        issues = [self._create_issue_with_completion_date("T1", "2023-01-08T00:00:00Z")] # Exactly on period_end_dt
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc) # Exclusive
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 0

    def test_issue_completed_on_period_start_inclusive(self, mock_config_throughput_done):
        issues = [self._create_issue_with_completion_date("T1", "2023-01-01T00:00:00Z")] # Exactly on period_start_dt
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 1

    def test_mixed_completion_criteria_and_timing(self, mock_config_throughput_done):
        done_statuses = config.THROUGHPUT_DONE_STATUSES
        issues = [
            self._create_issue_with_completion_date("T1", "2023-01-03T00:00:00Z"), # In period, by resdate
            self._create_issue_with_completion_date("T2", f"status:{'2023-01-06T00:00:00Z'}", done_statuses), # In period, by status
            self._create_issue_with_completion_date("T3", "2022-12-30T00:00:00Z"), # Before period
            self._create_issue_with_completion_date("T4", f"status:{'2023-01-08T01:00:00Z'}", done_statuses), # After period
        ]
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 2
        
    def test_invalid_period_date_types_raises_error(self):
        naive_dt = datetime(2023,1,1)
        aware_dt = datetime(2023,1,8, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="period_start_dt must be a timezone-aware datetime"):
            data_processor.calculate_throughput_for_period([], naive_dt, aware_dt)
        with pytest.raises(ValueError, match="period_end_dt must be a timezone-aware datetime"): # Corrected match string
            data_processor.calculate_throughput_for_period([], aware_dt, naive_dt)
        with pytest.raises(ValueError, match="period_end_dt must be after period_start_dt"):
            data_processor.calculate_throughput_for_period([], aware_dt, aware_dt) # End not after start

    def test_throughput_config_done_statuses_not_list(self, monkeypatch, caplog):
        # Test when config.THROUGHPUT_DONE_STATUSES is defined but not a list
        monkeypatch.setattr(config, "THROUGHPUT_DONE_STATUSES", "NotAList")
        issues = [self._create_issue_with_completion_date("T1", "2023-01-05T12:00:00Z")] # Will use resdate
        start_dt = datetime(2023, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2023, 1, 8, tzinfo=timezone.utc)
        
        assert data_processor.calculate_throughput_for_period(issues, start_dt, end_dt) == 1
        assert "config.THROUGHPUT_DONE_STATUSES is defined but not a list" in caplog.text