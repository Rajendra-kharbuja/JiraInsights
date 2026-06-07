# Project Metrics & Data Specifications: Jira Insights

This document details the key data inputs, calculated metrics, and their interpretations used within the **Jira Insights** project. Its purpose is to provide a clear, shared understanding of *what* data is fetched from Jira, *how* it's processed, and *what the calculated metrics signify* in the context of the project's goals (supporting Scrum Master insights).

**Crucial Note:** The accuracy of metrics like Cycle Time, Throughput, and WIP heavily depends on the correct mapping of specific Jira statuses to logical workflow stages (e.g., 'Cycle Start', 'Cycle End', 'Done', 'Active WIP') within **`config.py`**. Users **must** configure these mappings.

## I. Core Data Inputs

### Data Source 1: Jira REST API
*   **Description:** Primary source for all ticket information. Accessed via `src/jira_connector.py`.
*   **Key Data Points Fetched (by `fetch_issues_by_jql`):**
    *   **Default Fields (defined in `config.DEFAULT_JIRA_FIELDS_TO_FETCH`):** Includes `id`, `key`, `summary`, `issuetype`, `status`, `created`, `resolutiondate`, `project`. Other fields specifiable.
    *   **Status Transition History (Changelog):** Fetched via `expand=changelog`. Parsed into `status_transitions` key in each issue dict (List of Dicts: `timestamp`, `from_status`, `to_status`), chronologically sorted.
*   **Update Frequency:** On-demand.
*   **Access Method:** Authenticated REST API GET requests to `/search` with JQL using the configured Jira email address and API token. Handles pagination and `expand=changelog`.

### Data Source 2: Offline Demo Sample Data
*   **Description:** Committed Jira-like issue data used for offline demo and test workflows. Loaded via `src/sample_data_loader.py`.
*   **File:** `sample_data/demo_issues.json`.
*   **Key Data Points:** Uses the same issue dictionary shape expected by the processing layer: top-level `id` and `key`, nested `fields` values, and parsed `status_transitions`.
*   **Update Frequency:** Static sample data, refreshed manually when demo scenarios need to represent new metric or data-quality cases.
*   **Access Method:** Local JSON file. No `.env`, Jira credentials, or network access required.

## II. Calculated Metrics / Indicators

### Metric 1: Cycle Time
*   **Purpose:** Measures active work time on an issue.
*   **Data Required (from each issue dict):** `status_transitions`.
*   **Configuration Required (in `config.py`):** `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`.
*   **Calculation Logic (`src/data_processor.py` - `calculate_cycle_time`):**
    1.  Identifies first transition *to* a `CYCLE_START_STATUSES` status (`start_time`).
    2.  Identifies first subsequent transition *to* a `CYCLE_END_STATUSES` status (`end_time`).
    3.  Cycle Time = `end_time - start_time`. Timestamps parsed as UTC.
    4.  Returns `None` if a valid start/end pair is not found.
*   **Output Unit:** Configurable (default "days", float). Stored in `issue['cycle_time']`, `issue['cycle_time_unit']`.
*   **Interpretation:** Shorter indicates faster flow. Variability highlights inconsistencies.

### Metric 2: Lead Time
*   **Purpose:** Total time from issue creation to resolution.
*   **Data Required (from each issue dict, via `fields` object):**
    *   `created` (Jira: `fields.created`)
    *   `resolutiondate` (Jira: `fields.resolutiondate`, nullable)
*   **Calculation Logic (`src/data_processor.py` - `calculate_lead_time`):**
    1.  Parses `created` and `resolutiondate` timestamps into UTC datetime objects.
    2.  Lead Time = `resolved_datetime - created_datetime`.
    3.  Returns `None` if either date is missing, unparseable, or `resolutiondate` < `created`.
*   **Output Unit:** Configurable (default "days", float). Stored in `issue['lead_time']`, `issue['lead_time_unit']`.
*   **Interpretation:** Overall responsiveness. Compare with Cycle Time to see queue/wait times.

### Metric 3: Throughput
*   **Purpose:** Rate of work completion.
*   **Data Required:** `resolutiondate` from `fields`, or `status_transitions` when `resolutiondate` is unavailable.
*   **Configuration Required (in `config.py`):** `THROUGHPUT_DONE_STATUSES`.
*   **Calculation Logic (`src/data_processor.py` - `get_completion_date`, `calculate_throughput_for_period`):**
    1.  Determines each issue's completion date using `fields.resolutiondate` first.
    2.  If `resolutiondate` is missing or invalid, uses the first transition *to* a configured `THROUGHPUT_DONE_STATUSES` status.
    3.  Counts issues whose completion date falls within the requested reporting period.
    4.  The reporting period is start-inclusive and end-exclusive: `[period_start_dt, period_end_dt)`.
    5.  Both period boundaries must be timezone-aware datetime objects.
*   **Output Unit:** Integer count for the requested period.
*   **Interpretation:** Indicates how many items were completed during a period. Useful for spotting delivery trends and pairing with cycle/lead time to understand flow health.

### Indicator 1: Data Quality Warnings
*   **Purpose:** Explains why a metric may be missing or unreliable so users can distinguish process signals from incomplete Jira data or workflow configuration gaps.
*   **Data Required:** Issue `fields.created`, `fields.resolutiondate`, `status_transitions`, and configured status mappings from `config.py`.
*   **Output Logic (`src/data_processor.py` - `build_data_quality_warnings`):**
    1.  Adds structured warning records to processed issues under `issue['data_quality_warnings']`.
    2.  Each warning has stable fields: `issue_key`, `code`, `message`, and `severity`.
    3.  Detects missing resolution dates.
    4.  Detects missing cycle start transitions and missing cycle end transitions after a valid cycle start.
    5.  Detects invalid `created`, `resolutiondate`, and status transition timestamps.
    6.  Detects empty cycle start, cycle end, and throughput done status mappings.
    7.  Detects logically inconsistent dates such as `resolutiondate` before `created`.
*   **Warning Codes:** `MISSING_RESOLUTION_DATE`, `MISSING_CYCLE_START`, `MISSING_CYCLE_END`, `INVALID_CREATED_TIMESTAMP`, `INVALID_RESOLUTION_TIMESTAMP`, `INVALID_TRANSITION_TIMESTAMP`, `EMPTY_CYCLE_START_STATUSES`, `EMPTY_CYCLE_END_STATUSES`, `EMPTY_THROUGHPUT_DONE_STATUSES`, `RESOLUTION_BEFORE_CREATED`.
*   **Interpretation:** Warnings should be reviewed before coaching conclusions are drawn. A slow metric may indicate flow friction; a missing metric with warnings usually indicates incomplete Jira data, missing changelog history, or workflow mapping configuration that needs attention.

### Metric 4: Work In Progress (WIP) Snapshot
*   **Purpose:** Number of items actively being worked on.
*   **Data Required:** Current status from each issue's `fields.status.name`.
*   **Configuration Required (in `config.py`):** `WIP_STATUSES`.
*   **Calculation Logic (`src/data_processor.py` - `calculate_wip_snapshot`):**
    1.  Reads configured active statuses from `config.WIP_STATUSES` unless explicit statuses are supplied.
    2.  Extracts each issue's current status.
    3.  Counts issues whose current status is in the active WIP status list.
    4.  Returns a structured snapshot with `count`, configured `statuses`, matching `issues`, and `status_counts`.
*   **Output Unit:** Integer snapshot count plus grouped status counts.
*   **Interpretation:** Indicates how much active work is in the system at report time. High WIP can point to multitasking, bottlenecks, or too many items started before completion.

## III. Aggregated Statuses / Outputs (If Applicable)

### Output Category 1: Issue Metric CSV Export
*   **Purpose:** Provides a flat, shareable issue-level output for inspection, spreadsheet analysis, and future report workflows.
*   **Data Required:** Processed issue dictionaries containing Jira `fields` data plus calculated `cycle_time`, `cycle_time_unit`, `lead_time`, and `lead_time_unit` values.
*   **Output Logic (`src/reporting.py` - `build_issue_metric_rows`, `write_metrics_csv`):**
    1.  Flattens common Jira fields into stable columns: `key`, `summary`, `issue_type`, `status`, `project_key`, `created`, and `resolutiondate`.
    2.  Includes calculated metric columns: `cycle_time`, `cycle_time_unit`, `lead_time`, and `lead_time_unit`.
    3.  Includes data-quality columns: `data_quality_warning_count` and `data_quality_warning_codes`.
    4.  Writes CSV files using `config.DEFAULT_OUTPUT_FILENAME` unless a caller provides a specific output path.
*   **Interpretation:** Intended as raw-but-readable issue metric detail. Empty metric values indicate that the calculation could not be completed for that issue with the available data and configuration.

### Output Category 2: Basic Console Metric Summary
*   **Purpose:** Gives a quick terminal-readable view of processed flow metrics.
*   **Data Required:** Processed issue dictionaries with calculated issue-level metrics.
*   **Output Logic (`src/reporting.py` - `print_metric_summary`):**
    1.  Counts analyzed issues.
    2.  Counts issues with a `resolutiondate`.
    3.  Calculates average cycle time and average lead time from numeric metric values only.
    4.  Displays `N/A` when no numeric values are available for a metric.
*   **Interpretation:** Useful for a fast sanity check or lightweight metric-only output.

### Output Category 3: Scrum Master Insight Summary
*   **Purpose:** Converts processed issue metrics into a deterministic, coaching-oriented summary that helps a Scrum Master decide where to inspect flow next.
*   **Data Required:** Processed issue dictionaries with calculated `cycle_time` and `lead_time` values. Optional throughput output requires a timezone-aware reporting period.
*   **Output Logic (`src/reporting.py` - `build_insight_summary`, `format_insight_summary`, `print_insight_summary`):**
    1.  Counts analyzed issues.
    2.  Counts completed issues using the same completion-date priority as throughput: `fields.resolutiondate` first, then configured done-status transitions when available.
    3.  Calculates average and median cycle time from numeric cycle-time values.
    4.  Calculates average and median lead time from numeric lead-time values.
    5.  Optionally calculates throughput for a supplied start-inclusive, end-exclusive reporting period.
    6.  Calculates a WIP snapshot using configured active statuses.
    7.  Lists the slowest cycle-time items as bottleneck candidates.
    8.  Groups structured data-quality warnings into observations. If issue-level warning records are unavailable, falls back to basic observations inferred from missing metric values.
*   **Interpretation:** Intended for Scrum Master review and coaching conversations. Slowest items are candidates for deeper inspection; data-quality observations clarify whether missing metrics reflect process behavior or incomplete Jira data/configuration.

### Output Category 4: CLI Analysis Output
*   **Purpose:** Provides a repeatable command-line path for offline demo and Jira-like JSON file analysis.
*   **Data Required:** Local Jira-like issue JSON data in the same issue dictionary shape used by the processing layer.
*   **Output Logic (`main.py`):**
    1.  `python3 main.py demo` loads the committed sample dataset, applies demo workflow status mappings, processes metrics, and prints the Scrum Master insight summary for the sample reporting period.
    2.  `python3 main.py analyze-file <path>` loads a user-provided Jira-like JSON file, processes metrics using current `config.py` status mappings, and prints the same insight summary.
    3.  `analyze-file` accepts optional `--period-start` and `--period-end` values to include throughput in the summary.
    4.  Both commands accept `--csv-output` for issue detail CSV export and `--json-output` for full MVP report JSON export.
*   **Interpretation:** Intended as the first releasable user workflow. It does not require `.env`, Jira credentials, or network access.

### Output Category 5: MVP Report Payload
*   **Purpose:** Packages the most useful MVP information into one stable structure suitable for repeated Scrum Master review, CLI export, and future report formatting.
*   **Data Required:** Processed issue dictionaries with metrics and optional `data_quality_warnings`.
*   **Output Logic (`src/reporting.py` - `build_mvp_report`, `format_mvp_report`, `write_report_json`):**
    1.  Builds a `summary` using the Scrum Master insight summary structure.
    2.  Includes `bottleneck_candidates` from the slowest cycle-time items.
    3.  Includes `data_quality.observations` and `data_quality.warning_counts` grouped by warning code.
    4.  Includes `issue_details` using the issue metric CSV row shape.
    5.  Writes JSON with datetime values converted to ISO 8601 strings.
*   **Interpretation:** Intended as the releasable MVP report contract. The JSON payload is comprehensive, while CSV gives a flat issue-level view for spreadsheet inspection.

### Output Category 6: Cumulative Flow Diagram (CFD) Data (Planned Feature)
*   **Purpose:** To visualize workflow.
*   **Data Required:** Parsed `status_transitions`.
*   **Configuration Required (in `config.py`):** `CFD_COLUMN_MAPPING: dict[str, list[str]]`.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

### Output Category 7: Sprint Summary Report Data (Planned Feature)
*   **Purpose:** Metrics for a specific Scrum sprint.
*   **Data Required:** Sprint information, issue completion, `status_transitions`.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

---
*This document MUST be updated whenever new data sources are added, metrics are defined/modified, calculation logic changes, or configuration related to metrics is altered. Consistency between this document, `config.py`, and relevant Python modules is critical.*
