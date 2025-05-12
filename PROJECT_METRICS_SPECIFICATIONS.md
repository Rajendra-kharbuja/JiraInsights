# Project Metrics & Data Specifications: Jira Insights

This document details the key data inputs, calculated metrics, and their interpretations used within the **Jira Insights** project. Its purpose is to provide a clear, shared understanding of *what* data is fetched from Jira, *how* it's processed, and *what the calculated metrics signify* in the context of the project's goals (supporting Scrum Master insights).

**Crucial Note:** The accuracy of metrics like Cycle Time heavily depends on the correct mapping of specific Jira statuses to logical workflow stages (e.g., 'Cycle Start', 'Cycle End') within [`config.py`](config.py).

## I. Core Data Inputs

### Data Source 1: Jira REST API
*   **Description:** Primary source for all ticket, sprint, and board/project information. Accessed via standard Jira Cloud/Server REST APIs using JQL queries.
*   **Key Data Points Used (Initial Scope - Fetched via API):**
    *   `Issue ID` (`id`): Unique Jira identifier.
    *   `Issue Key` (`key`): Human-readable key (e.g., PROJ-123).
    *   `Issue Type` (`fields.issuetype.name`): (e.g., Story, Bug, Task). For filtering and analysis.
    *   `Status` (`fields.status.name`): Current status of the issue.
    *   `Resolution` (`fields.resolution.name`, nullable): The resolution state (e.g., 'Done', 'Fixed'). Used for Lead Time if `Resolution Date` is reliable.
    *   `Created Date` (`fields.created`): ISO 8601 timestamp when the issue was created. Used for Lead Time.
    *   `Resolution Date` (`fields.resolutiondate`, nullable): ISO 8601 timestamp when the issue resolution was set. Used for Lead Time, Throughput.
    *   `Status Transition History (Changelog)` (`changelog` expansion): Contains history items. Crucial items have `fieldId == 'status'`, providing `fromString`/`toString` status values and `created` timestamp for the transition. **Required for Cycle Time calculation.**
    *   `Sprint Information` (`fields.sprint`, `fields.closedSprints`): Details of sprints an issue was part of (ID, name, start/end dates, state). Used for sprint-based analysis (future).
    *   `(Future)` `Assignee` (`fields.assignee.displayName`), `Reporter` (`fields.reporter.displayName`), `Labels` (`fields.labels`), `Components` (`fields.components.name`).
    *   `(Future)` `Custom Fields` (e.g., Story Points, Priority) - requires explicit configuration of field IDs/names.
*   **Update Frequency:** Data is fetched on-demand when the tool is run.
*   **Access Method:** Authenticated REST API GET requests (using `requests` library, likely targeting the `/search` endpoint with JQL). Requires handling pagination (`maxResults`, `startAt`). Fetching `changelog` requires specific `expand` parameter.

## II. Calculated Metrics / Indicators
<!-- For each key metric the system calculates, define it -->

### Metric 1: Cycle Time
*   **Purpose:** To measure the time it takes for a work item to move through the 'active' part of the workflow (from starting work to ready for release/done). Helps understand process efficiency and identify bottlenecks within the active development flow.
*   **Calculation:** For each completed issue: `Timestamp(Entered 'Cycle End Status') - Timestamp(Entered 'Cycle Start Status')`.
    *   The specific Jira status names corresponding to **'Cycle Start Status'** (e.g., 'In Progress') and **'Cycle End Status'** (e.g., 'Ready for QA', 'Resolved', 'Done') **MUST be configurable** in [`config.py`](config.py).
    *   Calculation relies on parsing the `Status Transition History (Changelog)`. It finds the *first* timestamp an issue transitioned *into* the configured 'Cycle Start Status' and the *first* timestamp it transitioned *into* the configured 'Cycle End Status' *after* entering the start status.
    *   Typically aggregated as Average, Median, and Percentiles (e.g., 50th, 85th, 95th) over a reporting period.
    *   Handled in [`data_processor.py`](src/data_processor.py).
*   **Interpretation:**
    *   Shorter Median/Average: Generally indicates faster processing once work begins.
    *   High Variance / Large difference between 85th percentile and Median: Suggests unpredictability, delays, or blockers affecting a significant portion of items.
    *   Trend (Rising/Falling): Shows changes in internal process efficiency over time.

### Metric 2: Lead Time
*   **Purpose:** To measure the total time elapsed from when an issue was created (logged in Jira) until it was resolved (marked with a resolution). Reflects the overall responsiveness of the system from request to completion.
*   **Calculation:** For each completed issue: `Timestamp(Resolution Date) - Timestamp(Created Date)`.
    *   Uses standard issue fields `fields.resolutiondate` and `fields.created`.
    *   Relies on `resolutiondate` being set reliably when work is considered 'Done'.
    *   Typically aggregated as Average, Median, and Percentiles over a reporting period.
    *   Handled in [`data_processor.py`](src/data_processor.py).
*   **Interpretation:**
    *   Shorter Median/Average: Indicates faster overall delivery from the time of request.
    *   Difference vs. Cycle Time: Can highlight significant time spent waiting in the backlog ('To Do' queue) before active work starts.
    *   Trend (Rising/Falling): Shows changes in overall delivery capability over time.

### Metric 3: Throughput
*   **Purpose:** To measure the rate at which the team completes work items. Indicates the team's delivery capacity or output rate.
*   **Calculation:** Count of issues transitioned to a 'Done' state (i.e., having a `Resolution Date` set or entering a specific 'Final Status' configured in [`config.py`](config.py)) within a specific time period (e.g., per week, per month, per sprint).
    *   Requires `Resolution Date` or analysis of the `Status Transition History` for entering the final configured status.
    *   The time period for aggregation (e.g., weekly) should be configurable or determined based on reporting needs.
    *   Handled in [`data_processor.py`](src/data_processor.py) and aggregated in [`reporting.py`](src/reporting.py).
*   **Interpretation:**
    *   Higher Value: Indicates more items completed in the period.
    *   Stability: Consistent throughput suggests a predictable delivery cadence. Fluctuations should be investigated.
    *   Trend (Rising/Falling): Shows changes in team capacity or the impact of process changes, team size changes, etc.

### Metric 4: Work In Progress (WIP) (Planned Feature)
*   **Purpose:** To track the number of items being actively worked on at a specific point in time or averaged over a period. Helps visualize bottlenecks, understand team focus, and relates to Little's Law (Avg Cycle Time = Avg WIP / Avg Throughput).
*   **Calculation (Snapshot):** Count of issues whose current status is *between* the configured 'Cycle Start Status' (inclusive) and 'Cycle End Status' (exclusive).
*   **Calculation (Average over Period):** Sample the snapshot WIP at regular intervals (e.g., daily) and average the count over the reporting period. Requires analyzing historical status or taking daily snapshots.
    *   Requires configuration of statuses considered 'In Progress' in [`config.py`](config.py).
    *   Handled in [`data_processor.py`](src/data_processor.py).
*   **Interpretation:**
    *   High WIP: Can indicate multitasking, context switching, hidden bottlenecks, and is often correlated with longer cycle times.
    *   Low WIP: Generally desirable (following Lean/Kanban principles), promotes focus and faster flow.
    *   Trend: Changes in WIP levels can be compared against changes in throughput and cycle time.

## III. Aggregated Statuses / Outputs (If Applicable)

### Output Category 1: Cumulative Flow Diagram (CFD) Data (Planned Feature)
*   **Purpose:** To provide data points necessary for visualizing workflow stability, WIP levels across stages, approximate average cycle time, and identifying bottleneck stages over time.
*   **Contributing Metrics:** Status Transition History (timestamps, to/from statuses), list of configured workflow stages/columns.
*   **Aggregation Logic:**
    1.  Define logical CFD columns in [`config.py`](config.py) and map specific Jira statuses to each column (e.g., {'To Do': ['Open', 'Backlog'], 'Dev': ['In Progress', 'Code Review'], 'Test': ['In QA'], 'Done': ['Resolved', 'Closed']}).
    2.  For each day within a reporting period, count the number of issues residing in each mapped CFD column *at the end of that day*. This requires processing the full status transition history for all relevant issues up to that day.
    *   Output format: Typically CSV/JSON with columns like `Date`, `Column_Name`, `Issue_Count`.
    *   Handled in [`data_processor.py`](src/data_processor.py) / [`reporting.py`](src/reporting.py).
*   **Interpretation of Statuses (when visualized):**
    *   **Widening Bands:** A band for a specific column getting thicker over time indicates items are entering that stage faster than they are leaving, highlighting a potential bottleneck.
    *   **Slope of 'Done' Band:** Represents Throughput (steeper slope = higher throughput).
    *   **Horizontal Distance:** The average horizontal distance between the top of the 'Cycle Start' band(s) and the top of the 'Done' band approximates the average Cycle Time.
    *   **Vertical Distance:** The total vertical distance between the top of the first active band and the top of the 'Done' band represents the total WIP.

### Output Category 2: Sprint Summary Report Data (Planned Feature)
*   **Purpose:** To provide key metrics related to a specific, completed Scrum sprint.
*   **Contributing Metrics:** Throughput (for the sprint duration), Cycle Time/Lead Time (for items completed *within* the sprint), Scope Change (items added/removed after sprint start), potentially Story Points committed vs. completed.
*   **Aggregation Logic:**
    1.  Identify issues associated with a specific Sprint ID.
    2.  Fetch sprint details (start/end dates).
    3.  Filter issue data based on sprint ID and completion date within sprint timeframe.
    4.  Calculate standard metrics (Throughput, Cycle/Lead Time) only for relevant issues and the sprint's time window.
    5.  Analyze issue history to identify scope changes (added to sprint after start date).
    *   Handled in [`data_processor.py`](src/data_processor.py) / [`reporting.py`](src/reporting.py).
*   **Interpretation:** Helps assess sprint predictability, delivery against commitment, flow within the sprint context, and identify patterns related to scope creep or estimation accuracy.

---
*This document MUST be updated whenever new data sources are added, metrics are defined/modified, calculation logic changes, or configuration related to metrics (like status mappings) is altered. Maintaining consistency between this document, [`config.py`](config.py), and [`data_processor.py`](src/data_processor.py) is critical.*