# src/data_processor.py
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union # Added timedelta, Union
# Attempt to import config from project root
try:
    import config
except ImportError:
    logging.getLogger(__name__).error(
        "Could not import 'config'. Ensure project root is in PYTHONPATH."
    )
    # Fallback for testing if config is not found, though tests should mock/set config attributes
    class MockConfig: # Define a mock config for basic functionality if import fails
        CYCLE_START_STATUSES = []
        CYCLE_END_STATUSES = []
        THROUGHPUT_DONE_STATUSES = None # Ensure this exists for getattr
    config = MockConfig()
import logging

logger = logging.getLogger(__name__)


WARNING_MISSING_RESOLUTION_DATE = "MISSING_RESOLUTION_DATE"
WARNING_MISSING_CYCLE_START = "MISSING_CYCLE_START"
WARNING_MISSING_CYCLE_END = "MISSING_CYCLE_END"
WARNING_INVALID_CREATED_TIMESTAMP = "INVALID_CREATED_TIMESTAMP"
WARNING_INVALID_RESOLUTION_TIMESTAMP = "INVALID_RESOLUTION_TIMESTAMP"
WARNING_INVALID_TRANSITION_TIMESTAMP = "INVALID_TRANSITION_TIMESTAMP"
WARNING_EMPTY_CYCLE_START_STATUSES = "EMPTY_CYCLE_START_STATUSES"
WARNING_EMPTY_CYCLE_END_STATUSES = "EMPTY_CYCLE_END_STATUSES"
WARNING_EMPTY_THROUGHPUT_DONE_STATUSES = "EMPTY_THROUGHPUT_DONE_STATUSES"
WARNING_RESOLUTION_BEFORE_CREATED = "RESOLUTION_BEFORE_CREATED"


def _build_warning(
    issue_key: str,
    code: str,
    message: str,
    severity: str = "warning",
) -> Dict[str, str]:
    return {
        "issue_key": issue_key,
        "code": code,
        "message": message,
        "severity": severity,
    }


def _parse_iso_datetime(timestamp_str: Optional[str]) -> Optional[datetime]:
    """
    Parses an ISO 8601 timestamp string into a timezone-aware datetime object (UTC).
    """
    if not timestamp_str:
        return None
    try:
        if timestamp_str.endswith("+0000"):
            timestamp_str = timestamp_str[:-5] + "Z"
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError as e:
        logger.error(f"Error parsing timestamp string '{timestamp_str}': {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected error parsing timestamp string '{timestamp_str}': {e}")
        return None


def calculate_cycle_time(
    status_transitions: List[Dict[str, Any]],
    start_statuses: List[str],
    end_statuses: List[str],
    output_unit: str = "days"
) -> Optional[float]:
    """Calculates cycle time."""
    if not status_transitions or not start_statuses or not end_statuses:
        logger.debug("CT: Insufficient data for calculation.")
        return None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    for transition in status_transitions:
        current_to_status = transition.get("to_status")
        current_timestamp_str = transition.get("timestamp")
        if start_time is None:
            if current_to_status in start_statuses:
                parsed_time = _parse_iso_datetime(current_timestamp_str)
                if parsed_time:
                    start_time = parsed_time
                    logger.debug(f"CT: Start event. Status: '{current_to_status}', Time: {start_time.isoformat()}")
                else:
                    logger.warning(f"CT: Start status '{current_to_status}' found but invalid timestamp: {current_timestamp_str}")
        elif end_time is None:
            current_transition_time = _parse_iso_datetime(current_timestamp_str)
            if current_transition_time and start_time and current_transition_time >= start_time:
                if current_to_status in end_statuses:
                    end_time = current_transition_time
                    logger.debug(f"CT: End event. Status: '{current_to_status}', Time: {end_time.isoformat()}")
                    break
            elif not current_transition_time:
                logger.warning(f"CT: Potential end status '{current_to_status}' found but invalid timestamp: {current_timestamp_str}")
    if start_time and end_time:
        if end_time < start_time:
            logger.warning(f"CT calc: End time ({end_time}) before start time ({start_time}). Invalid.")
            return None
        duration_timedelta = end_time - start_time
        duration_seconds = duration_timedelta.total_seconds()
        if output_unit == "days": return duration_seconds / (60 * 60 * 24)
        if output_unit == "hours": return duration_seconds / (60 * 60)
        if output_unit == "minutes": return duration_seconds / 60
        if output_unit == "seconds": return duration_seconds
        logger.error(f"Invalid output_unit for cycle time: '{output_unit}'. Defaulting to days.")
        return duration_seconds / (60 * 60 * 24)
    else:
        logger.debug("CT: Valid start/end pair not found.")
        return None


def calculate_lead_time(
    created_timestamp_str: Optional[str],
    resolved_timestamp_str: Optional[str],
    output_unit: str = "days"
) -> Optional[float]:
    """Calculates lead time."""
    if not created_timestamp_str:
        logger.debug("LT: Created timestamp is missing.")
        return None
    if not resolved_timestamp_str:
        logger.debug("LT: Resolved timestamp is missing.")
        return None
    created_dt = _parse_iso_datetime(created_timestamp_str)
    resolved_dt = _parse_iso_datetime(resolved_timestamp_str)
    if not created_dt:
        logger.warning(f"LT: Failed to parse created timestamp '{created_timestamp_str}'.")
        return None
    if not resolved_dt:
        logger.warning(f"LT: Failed to parse resolved timestamp '{resolved_timestamp_str}'.")
        return None
    if resolved_dt < created_dt:
        logger.warning(f"LT calc: Resolved time ({resolved_dt.isoformat()}) is before created time ({created_dt.isoformat()}). Invalid.")
        return None
    duration_timedelta: timedelta = resolved_dt - created_dt
    duration_seconds: float = duration_timedelta.total_seconds()
    if output_unit == "days": return duration_seconds / (60 * 60 * 24)
    if output_unit == "hours": return duration_seconds / (60 * 60)
    if output_unit == "minutes": return duration_seconds / 60
    if output_unit == "seconds": return duration_seconds
    logger.error(f"Invalid output_unit for lead time: '{output_unit}'. Defaulting to days.")
    return duration_seconds / (60 * 60 * 24)


def build_data_quality_warnings(
    issue_data: Dict[str, Any],
    cycle_start_statuses: Optional[List[str]] = None,
    cycle_end_statuses: Optional[List[str]] = None,
    throughput_done_statuses: Optional[List[str]] = None,
) -> List[Dict[str, str]]:
    """
    Builds structured data-quality warning records for one processed issue.

    Args:
        issue_data: A single Jira-like issue dictionary.
        cycle_start_statuses: Configured statuses that mark cycle-time start.
        cycle_end_statuses: Configured statuses that mark cycle-time end.
        throughput_done_statuses: Configured statuses that mark throughput done.

    Returns:
        A list of stable warning dictionaries.
    """
    issue_key = str(issue_data.get("key", "N/A_KEY"))
    fields = issue_data.get("fields", {}) or {}
    status_transitions = issue_data.get("status_transitions", []) or []
    warnings: List[Dict[str, str]] = []

    created_str = fields.get("created")
    resolution_str = fields.get("resolutiondate")
    created_dt = _parse_iso_datetime(created_str)
    resolution_dt = _parse_iso_datetime(resolution_str)

    if created_str and created_dt is None:
        warnings.append(_build_warning(
            issue_key,
            WARNING_INVALID_CREATED_TIMESTAMP,
            "Created timestamp is invalid; lead time cannot be trusted.",
        ))
    if not resolution_str:
        warnings.append(_build_warning(
            issue_key,
            WARNING_MISSING_RESOLUTION_DATE,
            "Resolution date is missing; lead time and completion detection may be limited.",
        ))
    elif resolution_dt is None:
        warnings.append(_build_warning(
            issue_key,
            WARNING_INVALID_RESOLUTION_TIMESTAMP,
            "Resolution date is invalid; lead time and completion detection may be limited.",
        ))
    if created_dt and resolution_dt and resolution_dt < created_dt:
        warnings.append(_build_warning(
            issue_key,
            WARNING_RESOLUTION_BEFORE_CREATED,
            "Resolution date is before created date; lead time is logically inconsistent.",
        ))

    for transition in status_transitions:
        timestamp_str = transition.get("timestamp")
        if timestamp_str and _parse_iso_datetime(timestamp_str) is None:
            warnings.append(_build_warning(
                issue_key,
                WARNING_INVALID_TRANSITION_TIMESTAMP,
                "A status transition timestamp is invalid; cycle time may be incomplete.",
            ))
            break

    if not cycle_start_statuses:
        warnings.append(_build_warning(
            issue_key,
            WARNING_EMPTY_CYCLE_START_STATUSES,
            "Cycle start statuses are not configured; cycle time cannot be calculated.",
        ))
    if not cycle_end_statuses:
        warnings.append(_build_warning(
            issue_key,
            WARNING_EMPTY_CYCLE_END_STATUSES,
            "Cycle end statuses are not configured; cycle time cannot be calculated.",
        ))
    if not throughput_done_statuses:
        warnings.append(_build_warning(
            issue_key,
            WARNING_EMPTY_THROUGHPUT_DONE_STATUSES,
            "Throughput done statuses are not configured; status-based completion fallback is disabled.",
        ))

    if cycle_start_statuses and cycle_end_statuses:
        cycle_start_time = None
        for transition in status_transitions:
            transition_time = _parse_iso_datetime(transition.get("timestamp"))
            to_status = transition.get("to_status")
            if cycle_start_time is None and to_status in cycle_start_statuses:
                if transition_time:
                    cycle_start_time = transition_time
                continue
            if (
                cycle_start_time is not None
                and transition_time
                and transition_time >= cycle_start_time
                and to_status in cycle_end_statuses
            ):
                break
        else:
            if cycle_start_time is None:
                warnings.append(_build_warning(
                    issue_key,
                    WARNING_MISSING_CYCLE_START,
                    "No cycle start transition was found; cycle time cannot be calculated.",
                ))
            else:
                warnings.append(_build_warning(
                    issue_key,
                    WARNING_MISSING_CYCLE_END,
                    "No cycle end transition was found after cycle start; cycle time is incomplete.",
                ))

    return warnings

# --- NEW HELPER FUNCTION ---
def get_completion_date(
    issue_data: Dict[str, Any],
    throughput_done_statuses: Optional[List[str]] = None # Explicitly allow None
) -> Optional[datetime]:
    """
    Determines the completion date of an issue for throughput calculation.
    Priority:
    1. `resolutiondate` from issue fields.
    2. If no `resolutiondate`, and `throughput_done_statuses` are provided and not empty,
       the timestamp of the first entry into one of these statuses.

    Args:
        issue_data: A single issue dictionary.
        throughput_done_statuses: A list of status names considered "done".

    Returns:
        A timezone-aware datetime object (UTC) of completion, or None.
    """
    issue_key = issue_data.get('key', 'N/A_KEY') # For logging
    issue_fields = issue_data.get("fields", {})
    
    # Priority 1: resolutiondate
    resolved_str = issue_fields.get("resolutiondate")
    if resolved_str:
        resolved_dt = _parse_iso_datetime(resolved_str)
        if resolved_dt:
            logger.debug(f"Issue {issue_key}: Completion via resolutiondate: {resolved_dt.isoformat()}")
            return resolved_dt
        else:
            # Log warning but continue to check status transitions if resolutiondate is bad
            logger.warning(f"Issue {issue_key}: Had resolutiondate '{resolved_str}' but failed to parse.")

    # Priority 2: Status transition to a THROUGHOUT_DONE_STATUS
    # Ensure throughput_done_statuses is a list and not empty
    if isinstance(throughput_done_statuses, list) and throughput_done_statuses:
        status_transitions = issue_data.get("status_transitions", [])
        if status_transitions: # Only proceed if there are transitions
            # For throughput, typically interested in the *first* time it enters a done state.
            for transition in status_transitions:
                to_status = transition.get("to_status")
                if to_status in throughput_done_statuses:
                    timestamp_str = transition.get("timestamp")
                    completed_dt = _parse_iso_datetime(timestamp_str)
                    if completed_dt:
                        logger.debug(f"Issue {issue_key}: Completion via status transition to '{to_status}' at {completed_dt.isoformat()}")
                        return completed_dt
                    else:
                        logger.warning(f"Issue {issue_key}: Transitioned to done status '{to_status}' "
                                       f"but timestamp '{timestamp_str}' was unparseable. Cannot use this for completion date.")
                        # If one done transition has a bad timestamp, we might not want to trust it.
                        # Depending on strictness, could return None here or continue searching other transitions.
                        # For now, if a 'done' transition has a bad timestamp, we don't count it.
                        return None 
    
    logger.debug(f"Issue {issue_key}: No completion date found based on available criteria.")
    return None


def _current_status_name(issue_data: Dict[str, Any]) -> Optional[str]:
    fields = issue_data.get("fields", {}) or {}
    status = fields.get("status")
    if isinstance(status, dict):
        status_name = status.get("name")
        return str(status_name) if status_name is not None else None
    if status is None:
        return None
    return str(status)


def calculate_wip_snapshot(
    issues_data: List[Dict[str, Any]],
    wip_statuses: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Calculates a current work-in-progress snapshot from issue statuses.

    Args:
        issues_data: A list of issue dictionaries.
        wip_statuses: Status names considered active WIP. If None, uses
            config.WIP_STATUSES.

    Returns:
        A deterministic dictionary containing the WIP count, configured statuses,
        matching issue summaries, and counts grouped by current status.
    """
    if wip_statuses is None:
        configured_statuses = getattr(config, "WIP_STATUSES", None)
    else:
        configured_statuses = wip_statuses

    if configured_statuses is not None and not isinstance(configured_statuses, list):
        logger.warning("WIP_STATUSES is defined but not a list. WIP snapshot will be empty.")
        configured_statuses = []

    active_statuses = [str(status) for status in (configured_statuses or [])]
    if not active_statuses:
        logger.warning("WIP statuses are empty. WIP snapshot will be 0.")

    active_status_set = set(active_statuses)
    active_issues: List[Dict[str, Any]] = []
    status_counts: Dict[str, int] = {}

    for issue in issues_data:
        status_name = _current_status_name(issue)
        if status_name in active_status_set:
            active_issues.append({
                "key": issue.get("key"),
                "summary": (issue.get("fields") or {}).get("summary"),
                "status": status_name,
            })
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

    active_issues.sort(key=lambda item: (item.get("status") or "", item.get("key") or ""))

    return {
        "count": len(active_issues),
        "statuses": active_statuses,
        "issues": active_issues,
        "status_counts": dict(sorted(status_counts.items())),
    }

# --- NEW FUNCTION ---
def calculate_throughput_for_period(
    issues_data: List[Dict[str, Any]],
    period_start_dt: datetime,
    period_end_dt: datetime
) -> int:
    """
    Calculates throughput (count of completed issues) for a single specified period.
    The period is [period_start_dt, period_end_dt).

    Args:
        issues_data: A list of issue dictionaries.
        period_start_dt: The inclusive start datetime of the period (timezone-aware).
        period_end_dt: The exclusive end datetime of the period (timezone-aware).

    Returns:
        The number of issues completed within the specified period.
    """
    if not (isinstance(period_start_dt, datetime) and period_start_dt.tzinfo is not None):
        logger.error("calculate_throughput_for_period: period_start_dt must be a timezone-aware datetime.")
        raise ValueError("period_start_dt must be a timezone-aware datetime.")
    if not (isinstance(period_end_dt, datetime) and period_end_dt.tzinfo is not None): # Corrected to check for tzinfo
        logger.error("calculate_throughput_for_period: period_end_dt must be a timezone-aware datetime.")
        raise ValueError("period_end_dt must be a timezone-aware datetime.")
    if period_end_dt <= period_start_dt:
        logger.error("calculate_throughput_for_period: period_end_dt must be after period_start_dt.")
        raise ValueError("period_end_dt must be after period_start_dt.")


    completed_count = 0
    
    cfg_throughput_done_statuses = getattr(config, 'THROUGHPUT_DONE_STATUSES', None)
    if cfg_throughput_done_statuses is not None and not isinstance(cfg_throughput_done_statuses, list):
        logger.warning("config.THROUGHPUT_DONE_STATUSES is defined but not a list. It will be ignored for throughput calculation.")
        cfg_throughput_done_statuses = None # Treat as not configured if malformed

    for issue in issues_data:
        completion_date = get_completion_date(issue, cfg_throughput_done_statuses)
        if completion_date:
            # Ensure completion_date is comparable with period boundaries (both should be aware)
            if period_start_dt <= completion_date < period_end_dt:
                completed_count += 1
    
    logger.info(f"Throughput for period [{period_start_dt.isoformat()}, {period_end_dt.isoformat()}): {completed_count} issues.") # Changed to isoformat for full date-time
    return completed_count


def process_issues_for_metrics(
    issues_data: List[Dict[str, Any]],
    cycle_time_output_unit: str = "days",
    lead_time_output_unit: str = "days"
) -> List[Dict[str, Any]]:
    """Processes issues to add cycle time and lead time metrics."""
    cfg_cycle_start = getattr(config, 'CYCLE_START_STATUSES', None)
    cfg_cycle_end = getattr(config, 'CYCLE_END_STATUSES', None)
    cfg_throughput_done_statuses = getattr(config, 'THROUGHPUT_DONE_STATUSES', None)
    can_calc_cycle_time = True
    if cfg_cycle_start is None or cfg_cycle_end is None:
        logger.error("CT Config: CYCLE_START_STATUSES or CYCLE_END_STATUSES not found in config.")
        can_calc_cycle_time = False
    elif not cfg_cycle_start or not cfg_cycle_end:
        logger.warning("CT Config: CYCLE_START_STATUSES or CYCLE_END_STATUSES are empty in config. CT not calculated.")
        can_calc_cycle_time = False
    
    for issue in issues_data:
        if can_calc_cycle_time:
            status_transitions = issue.get("status_transitions", [])
            cycle_time = calculate_cycle_time(
                status_transitions,
                cfg_cycle_start if isinstance(cfg_cycle_start, list) else [],
                cfg_cycle_end if isinstance(cfg_cycle_end, list) else [],
                output_unit=cycle_time_output_unit
            )
            issue["cycle_time"] = cycle_time
            issue["cycle_time_unit"] = cycle_time_output_unit if cycle_time is not None else None
        else:
            issue["cycle_time"] = None
            issue["cycle_time_unit"] = None

        issue_fields = issue.get("fields", {})
        created_str = issue_fields.get("created")
        resolved_str = issue_fields.get("resolutiondate")
        lead_time = calculate_lead_time(
            created_str, resolved_str, output_unit=lead_time_output_unit
        )
        issue["lead_time"] = lead_time
        issue["lead_time_unit"] = lead_time_output_unit if lead_time is not None else None
        issue["data_quality_warnings"] = build_data_quality_warnings(
            issue,
            cfg_cycle_start if isinstance(cfg_cycle_start, list) else [],
            cfg_cycle_end if isinstance(cfg_cycle_end, list) else [],
            cfg_throughput_done_statuses
            if isinstance(cfg_throughput_done_statuses, list) else [],
        )
            
    return issues_data

# Example usage (optional, for direct testing of this module if needed)
# if __name__ == "__main__":
#     # Create some mock issue data
#     mock_issues = [
#         {
#             "key": "TEST-1",
#             "fields": {"created": "2023-01-01T00:00:00Z", "resolutiondate": "2023-01-10T00:00:00Z"},
#             "status_transitions": [
#                 {"timestamp": "2023-01-02T00:00:00Z", "from_status": "Open", "to_status": "In Progress"},
#                 {"timestamp": "2023-01-08T00:00:00Z", "from_status": "In Progress", "to_status": "Resolved"}
#             ]
#         },
#         {
#             "key": "TEST-2",
#             "fields": {"created": "2023-01-05T00:00:00Z", "resolutiondate": "2023-01-12T00:00:00Z"},
#             "status_transitions": [] # No status transitions for cycle time testing
#         },
#         {
#             "key": "TEST-3", # Resolved by status, no resolutiondate
#             "fields": {"created": "2023-01-10T00:00:00Z", "resolutiondate": None},
#             "status_transitions": [
#                 {"timestamp": "2023-01-11T00:00:00Z", "from_status": "Open", "to_status": "Done"}
#             ]
#         }
#     ]

#     # Mock config for testing
#     config.CYCLE_START_STATUSES = ["In Progress"]
#     config.CYCLE_END_STATUSES = ["Resolved"]
#     config.THROUGHPUT_DONE_STATUSES = ["Resolved", "Done"]

#     # Test process_issues_for_metrics
#     processed = process_issues_for_metrics(list(mock_issues)) # Pass a copy
#     for p_issue in processed:
#         print(f"Issue: {p_issue['key']}, Cycle Time: {p_issue.get('cycle_time')} {p_issue.get('cycle_time_unit')}, "
#               f"Lead Time: {p_issue.get('lead_time')} {p_issue.get('lead_time_unit')}")
    
#     # Test calculate_throughput_for_period
#     period_start = datetime(2023, 1, 1, tzinfo=timezone.utc)
#     period_end = datetime(2023, 1, 15, tzinfo=timezone.utc) # Exclusive end
#     throughput = calculate_throughput_for_period(processed, period_start, period_end)
#     print(f"Throughput from {period_start.date()} to {period_end.date()}: {throughput}")

#     period_start_2 = datetime(2023, 1, 10, tzinfo=timezone.utc)
#     period_end_2 = datetime(2023, 1, 11, tzinfo=timezone.utc) # Catches TEST-1
#     throughput_2 = calculate_throughput_for_period(processed, period_start_2, period_end_2)
#     print(f"Throughput from {period_start_2.date()} to {period_end_2.date()}: {throughput_2}")
