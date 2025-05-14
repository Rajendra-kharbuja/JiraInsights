# Project Metrics & Data Specifications: Jira Insights

This document details the key data inputs, calculated metrics, and their interpretations used within the **Jira Insights** project. Its purpose is to provide a clear, shared understanding of *what* data is fetched from Jira, *how* it's processed, and *what the calculated metrics signify* in the context of the project's goals (supporting Scrum Master insights).

**Crucial Note:** The accuracy of metrics like Cycle Time heavily depends on the correct mapping of specific Jira statuses to logical workflow stages (e.g., 'Cycle Start', 'Cycle End') within `config.py`.

## I. Core Data Inputs

### Data Source 1: Jira REST API
*   **Description:** Primary source for all ticket, sprint, and board/project information. Accessed via standard Jira Cloud/Server REST APIs using JQL queries (via `src/jira_connector.py`).
*   **Key Data Points Fetched (by `fetch_issues_by_jql`):**
    *   **Default Fields (if `fields` argument is `None`):**
        *   `Issue ID` (Jira: `id`): Unique Jira identifier. Top-level field in issue JSON.
        *   `Issue Key` (Jira: `key`): Human-readable key. Top-level field in issue JSON.
        *   `Issue Type` (Jira: `fields.issuetype.name`): e.g., Story, Bug, Task.
        *   `Status` (Jira: `fields.status.name`): Current status of the issue.
        *   `Created Date` (Jira: `fields.created`): ISO 8601 timestamp when the issue was created.
        *   `Resolution Date` (Jira: `fields.resolutiondate`, nullable): ISO 8601 timestamp when the issue resolution was set.
    *   **Status Transition History (Changelog):**
        *   Fetched when `include_changelog=True` (default) in `fetch_issues_by_jql` by requesting the `changelog` field via the `expand` API parameter.
        *   The raw changelog data is parsed by `_parse_status_transitions` in `src/jira_connector.py`.
        *   **Parsed Output Structure (added to each issue dictionary under `status_transitions` key):**
            A `List[Dict[str, Any]]`, where each dictionary represents a single status change and has the following keys:
            *   `"timestamp"`: `str` - ISO 8601 timestamp of when the status change occurred.
            *   `"from_status"`: `Optional[str]` - The name of the status *before* this change (can be `None` for initial status setting).
            *   `"to_status"`: `str` - The name of the status *after* this change.
            *   The list is chronologically sorted by `timestamp`.
    *   **Note:** The `fetch_issues_by_jql` function allows specifying a custom list of other fields to be fetched. The raw JSON structure from Jira typically has `id`, `key` at the top level, and most other details under a `fields` object. The `changelog` is also a top-level object when expanded.
*   **Key Data Points (Planned for Future Fetching/Parsing):**
    *   `Sprint Information` (Jira: `fields.sprint`, `fields.closedSprints`).
    *   `Assignee`, `Reporter`, `Labels`, `Components`.
    *   `Custom Fields`.
*   **Update Frequency:** Data is fetched on-demand when the tool is run.
*   **Access Method:** Authenticated (Basic Auth) REST API GET requests to the `/search` endpoint with JQL. Handles pagination and `expand=changelog`.

## II. Calculated Metrics / Indicators
<!-- For each key metric the system calculates, define it -->

### Metric 1: Cycle Time (Planned)
*   **Purpose:** To measure the time it takes for a work item to move through the 'active' part of the workflow.
*   **Data Required:** Parsed `status_transitions` (List of Dicts: timestamp, from_status, to_status). Configurable 'Cycle Start' and 'Cycle End' statuses (from `config.py`).
*   **Calculation:** `Timestamp(Entered 'Cycle End Status') - Timestamp(Entered 'Cycle Start Status')` based on the `status_transitions` data.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 2: Lead Time (Planned)
*   **Purpose:** To measure the total time a customer (or requestor) waits for a work item.
*   **Data Required:** `Created Date` (fetched as `fields.created`), `Resolution Date` (fetched as `fields.resolutiondate`).
*   **Calculation:** `Timestamp(Resolution Date) - Timestamp(Created Date)`.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 3: Throughput (Planned)
*   **Purpose:** To measure the rate at which the team completes work items.
*   **Data Required:** `Resolution Date` or timestamp of entering a final 'Done' status (from `status_transitions`).
*   **Calculation:** Count of issues transitioned to a 'Done' state within a specific time period.
    *   Handled in `data_processor.py` / `reporting.py` (planned).
*   **Interpretation:** (As previously defined)

### Metric 4: Work In Progress (WIP) (Planned Feature)
*   **Purpose:** To track the number of items being actively worked on.
*   **Data Required:** Current `Status` of issues (fetched as `fields.status.name`). Configurable 'In Progress' statuses.
*   **Calculation:** Count of issues currently between 'Cycle Start Status' and 'Cycle End Status'.
    *   Handled in `data_processor.py` (planned).
*   **Interpretation:** (As previously defined)

## III. Aggregated Statuses / Outputs (If Applicable)

### Output Category 1: Cumulative Flow Diagram (CFD) Data (Planned Feature)
*   **Purpose:** To visualize workflow stability, WIP, cycle time, bottlenecks.
*   **Data Required:** Parsed `status_transitions`. Configured CFD column mappings.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

### Output Category 2: Sprint Summary Report Data (Planned Feature)
*   **Purpose:** To provide key metrics related to a specific Scrum sprint.
*   **Data Required:** Sprint information, issue completion within sprint, `status_transitions`.
*   **Aggregation Logic:** (As previously defined)
*   **Interpretation:** (As previously defined)

---
*This document MUST be updated whenever new data sources are added, metrics are defined/modified, calculation logic changes, or configuration related to metrics (like status mappings or default fetched fields/parsed data structures) is altered. Maintaining consistency between this document, `config.py`, and relevant Python modules is critical.*