# Project Metrics & Data Specifications: Jira Insights

This document details the key data inputs, calculated metrics, and their interpretations used within the **Jira Insights** project. Its purpose is to provide a clear, shared understanding of *what* data is fetched from Jira, *how* it's processed, and *what the calculated metrics signify* in the context of the project's goals (supporting Scrum Master insights).

**Crucial Note:** The accuracy of metrics like Cycle Time and Throughput heavily depends on the correct mapping of specific Jira statuses to logical workflow stages (e.g., 'Cycle Start', 'Cycle End', 'Done') within **`config.py`**. Users **must** configure these mappings.

## I. Core Data Inputs

### Data Source 1: Jira REST API
*   **Description:** Primary source for all ticket information. Accessed via `src/jira_connector.py`.
*   **Key Data Points Fetched (by `fetch_issues_by_jql`):**
    *   **Default Fields (defined in `config.DEFAULT_JIRA_FIELDS_TO_FETCH`):** Includes `id`, `key`, `summary`, `issuetype`, `status`, `created`, `resolutiondate`, `project`. Other fields specifiable.
    *   **Status Transition History (Changelog):** Fetched via `expand=changelog`. Parsed into `status_transitions` key in each issue dict (List of Dicts: `timestamp`, `from_status`, `to_status`), chronologically sorted.
*   **Update Frequency:** On-demand.
*   **Access Method:** Authenticated (Basic Auth) REST API GET requests to `/search` with JQL. Handles pagination and `expand=changelog`.

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

### Metric 3: Throughput (Planned)
*   **Purpose:** Rate of work completion.
*   **Data Required:** `Resolution Date` OR `status_transitions`.
*   **Configuration Required (in `config.py`):** `THROUGHPUT_DONE_STATUSES`.
*   **Calculation:** Count of issues reaching a 'Done' state within a time period.
    *   Handled in `src/data_processor.py` / `src/reporting.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 4: Work In Progress (WIP) (Planned Feature)
*   **Purpose:** Number of items actively being worked on.
*   **Data Required:** Current `Status`. Configured 'active' statuses.
*   **Calculation:** Count of issues in 'active' statuses.
    *   Handled in `src/data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

## III. Aggregated Statuses / Outputs (If Applicable)

### Output Category 1: Cumulative Flow Diagram (CFD) Data (Planned Feature)
*   **Purpose:** To visualize workflow.
*   **Data Required:** Parsed `status_transitions`.
*   **Configuration Required (in `config.py`):** `CFD_COLUMN_MAPPING: dict[str, list[str]]`.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

### Output Category 2: Sprint Summary Report Data (Planned Feature)
*   **Purpose:** Metrics for a specific Scrum sprint.
*   **Data Required:** Sprint information, issue completion, `status_transitions`.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

---
*This document MUST be updated whenever new data sources are added, metrics are defined/modified, calculation logic changes, or configuration related to metrics is altered. Consistency between this document, `config.py`, and relevant Python modules is critical.*