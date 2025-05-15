# Project Metrics & Data Specifications: Jira Insights

This document details the key data inputs, calculated metrics, and their interpretations used within the **Jira Insights** project. Its purpose is to provide a clear, shared understanding of *what* data is fetched from Jira, *how* it's processed, and *what the calculated metrics signify* in the context of the project's goals (supporting Scrum Master insights).

**Crucial Note:** The accuracy of metrics like Cycle Time and Throughput heavily depends on the correct mapping of specific Jira statuses to logical workflow stages (e.g., 'Cycle Start', 'Cycle End', 'Done') within **`config.py`**. Users **must** configure these mappings.

## I. Core Data Inputs

### Data Source 1: Jira REST API
*   **Description:** Primary source for all ticket information. Accessed via `src/jira_connector.py`.
*   **Key Data Points Fetched (by `fetch_issues_by_jql`):**
    *   **Default Fields (if `fields` argument is `None`, defined in `config.DEFAULT_JIRA_FIELDS_TO_FETCH`):**
        *   `Issue ID` (Jira: `id`)
        *   `Issue Key` (Jira: `key`)
        *   `Summary` (Jira: `fields.summary`)
        *   `Issue Type` (Jira: `fields.issuetype.name`)
        *   `Status` (Jira: `fields.status.name`)
        *   `Created Date` (Jira: `fields.created`)
        *   `Resolution Date` (Jira: `fields.resolutiondate`, nullable)
        *   `Project` (Jira: `fields.project` - object with key, name, etc.)
        *   Other fields can be specified dynamically.
    *   **Status Transition History (Changelog):**
        *   Fetched when `include_changelog=True` (default) by `fetch_issues_by_jql`.
        *   Parsed into a `status_transitions` key in each issue dictionary.
        *   **Structure:** `List[Dict["timestamp": str (ISO 8601), "from_status": Optional[str], "to_status": str]]`, chronologically sorted.
*   **Update Frequency:** Data is fetched on-demand.
*   **Access Method:** Authenticated (Basic Auth) REST API GET requests to `/search` with JQL. Handles pagination and `expand=changelog`.

## II. Calculated Metrics / Indicators

### Metric 1: Cycle Time (Planned)
*   **Purpose:** Time an item spends actively being worked on.
*   **Data Required:** Parsed `status_transitions`.
*   **Configuration Required (in `config.py`):**
    *   `CYCLE_START_STATUSES: list[str]` - List of Jira status names that define the start of the cycle.
    *   `CYCLE_END_STATUSES: list[str]` - List of Jira status names that define the end of the cycle.
*   **Calculation:** `Timestamp(Entered first CYCLE_END_STATUSES) - Timestamp(Entered first CYCLE_START_STATUSES)` for each issue, derived from its `status_transitions`.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 2: Lead Time (Planned)
*   **Purpose:** Total time from request to completion.
*   **Data Required:** `Created Date` (`fields.created`), `Resolution Date` (`fields.resolutiondate`).
*   **Calculation:** `Timestamp(Resolution Date) - Timestamp(Created Date)`.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 3: Throughput (Planned)
*   **Purpose:** Rate of work completion.
*   **Data Required:** `Resolution Date` OR `status_transitions` to identify entry into a 'Done' state.
*   **Configuration Required (in `config.py`):**
    *   `THROUGHPUT_DONE_STATUSES: list[str]` - List of Jira status names considered 'Done' for throughput. If empty, `resolutiondate` or `CYCLE_END_STATUSES` might be used as fallback (TBD).
*   **Calculation:** Count of issues reaching a 'Done' state (per `THROUGHPUT_DONE_STATUSES` or `resolutiondate`) within a specific time period.
    *   Handled in `data_processor.py` / `reporting.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 4: Work In Progress (WIP) (Planned Feature)
*   **Purpose:** Number of items actively being worked on.
*   **Data Required:** Current `Status` of issues.
*   **Configuration Required (in `config.py`):** Will likely use `CYCLE_START_STATUSES` and `CYCLE_END_STATUSES` or a separate WIP status list.
*   **Calculation:** Count of issues currently in statuses considered 'active work'.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

## III. Aggregated Statuses / Outputs (If Applicable)

### Output Category 1: Cumulative Flow Diagram (CFD) Data (Planned Feature)
*   **Purpose:** Visualize workflow.
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
*This document MUST be updated whenever new data sources are added, metrics are defined/modified, calculation logic changes, or configuration related to metrics (like status mappings, default fetched fields, or parsed data structures) is altered. Consistency between this document, `config.py`, and relevant Python modules is critical.*