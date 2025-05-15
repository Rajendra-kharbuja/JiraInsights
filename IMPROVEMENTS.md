# Project Improvements & Action Items: Jira Insights

This document tracks identified bugs, planned features, refactoring tasks, and other enhancements for the **Jira Insights** project. It serves as the primary backlog for development work, guiding the **Incremental Development Workflow**.

**Prioritization Legend:**
*   **[CRITICAL]**: Must be addressed immediately. Blocks core functionality or causes major errors.
*   **[High]**: Significant impact on core functionality, user experience, or project goals (often part of MVP).
*   **[Medium]**: Important improvements for robustness, usability, secondary features, or essential groundwork.
*   **[Low]**: Nice-to-haves, minor fixes, cosmetic changes, or future-proofing.
*   **[Idea]**: A potential feature or improvement not yet fully scoped or prioritized.

---

## I. Bugs / Issues
<!-- List known bugs -->
*   *(None identified yet)*

## II. Core Feature Development (MVP & Beyond)
<!-- List main features to be built -->
1.  **[High] [FEAT-001] Initial Project Structure Setup** (Target: Iteration 1)
    *   **Description:** Create the basic directory structure (`src`, `tests`), essential files (`main.py`, `config.py`, `requirements.txt`, `.gitignore`, `.env.example`), and all documentation templates (`README.md`, `PROJECT_PURPOSE.md`, `PROJECT_METRICS_SPECIFICATIONS.md`, `IMPROVEMENTS.md`, `GEMINI_MASTER_GUIDANCE.md`). Initialize Git repository.
    *   **Acceptance Criteria:** Project can be cloned, basic structure exists, documentation templates are present. `requirements.txt` includes initial libraries. `.gitignore` is present.
    *   **Status:** Done (Iteration 1)
    *   **Notes/Dependencies:** Initial project structure, configuration templates, `.gitignore`, and documentation files created. Foundational first step.

2.  **[High] [FEAT-002] Implement Jira Connection & Authentication** (Target: Iteration 1)
    *   **Description:** Create `src/jira_connector.py`. Implement a function/class that reads Jira URL, email, and **password** from `.env` variables. Include a method to test the connection (e.g., by making a simple API call like `/rest/api/3/myself`) using Basic Authentication. Handle basic connection errors gracefully.
    *   **Acceptance Criteria:** Can successfully authenticate against a Jira instance using credentials from `.env`. Returns a clear success/failure indication. Logs informative errors on failure. All unit tests pass.
    *   **Status:** Done (Iteration 1)
    *   **Notes/Dependencies:** Implemented Jira connection using Basic Authentication (Email/Password from .env). Includes loading credentials and a test connection function. All unit tests pass. Requires `.env` setup by the user.

3.  **[High] [FEAT-003] Fetch Basic Issue Data via JQL** (Target: Iteration 2)
    *   **Description:** Extend `src/jira_connector.py`. Add a function that accepts a JQL string and fetches issues using the Jira search API (`/rest/api/3/search`). Initially fetch key fields required for Lead Time and Throughput. Implement handling for API pagination.
    *   **Acceptance Criteria:** Can retrieve a list of issues matching a provided JQL query. Pagination correctly fetches all results. Returns structured data (list of dicts). Handles API errors. All unit tests pass.
    *   **Status:** Done (Iteration 2)
    *   **Notes/Dependencies:** Implemented function to fetch Jira issues by JQL, handling pagination and field selection. Default fields fetched defined in `config.py`. FEAT-002.

4.  **[High] [FEAT-004] Fetch Issue Changelog (Status Transitions)** (Target: Iteration 2)
    *   **Description:** Modify `fetch_issues_by_jql` in `src/jira_connector.py` to include `changelog` via `expand` parameter. Add parsing logic (`_parse_status_transitions`) to extract status transitions.
    *   **Acceptance Criteria:** Fetched issue data includes a `status_transitions` key with a sorted list of parsed status changes if `include_changelog=True`. All unit tests pass.
    *   **Status:** Done (Iteration 2)
    *   **Notes/Dependencies:** Modified 'fetch_issues_by_jql' to request 'changelog'. Implemented '_parse_status_transitions'. Parsed transitions added to issue dicts. FEAT-003. Crucial for Cycle Time.

5.  **[High] [FEAT-005] Implement Cycle Time Calculation** (Target: Iteration 3)
    *   **Description:** Create `src/data_processor.py`. Implement logic to calculate cycle time for each issue using parsed status transitions (from FEAT-004) and configurable 'Cycle Start'/'Cycle End' statuses (from `config.py` - ENH-001).
    *   **Acceptance Criteria:** Cycle time is calculated correctly. Handles various scenarios (multiple entries/exits, missing start/end). Returns duration or NaN/None. Unit tests pass.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-004, ENH-001.

6.  **[High] [FEAT-006] Implement Lead Time Calculation** (Target: Iteration 3)
    *   **Description:** Implement logic in `src/data_processor.py` to calculate lead time for each issue using the `fields.created` and `fields.resolutiondate` fields.
    *   **Acceptance Criteria:** Lead time is calculated correctly. Handles missing `resolutiondate`. Unit tests pass.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-003.

7.  **[Medium] [FEAT-007] Implement Throughput Calculation** (Target: Iteration 4)
    *   **Description:** Implement logic to calculate throughput (count of completed items per time period) using `resolutiondate` or `THROUGHPUT_DONE_STATUSES` from `config.py`.
    *   **Acceptance Criteria:** Throughput is calculated correctly for given time windows. Unit tests pass.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-003/FEAT-004, ENH-001.

8.  **[Medium] [FEAT-008] Implement Basic Console/CSV Output** (Target: Iteration 4)
    *   **Description:** Create `src/reporting.py`. Implement functions to output summary statistics and/or raw data with calculated metrics to console or CSV.
    *   **Acceptance Criteria:** Metrics can be viewed/exported. Output is configurable.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-005, FEAT-006, FEAT-007.

## III. Enhancements & Refinements
<!-- Improvements to existing features, usability, performance -->
1.  **[High] [ENH-001] Add Configuration for Cycle/Lead Time Statuses in `config.py`** (Target: Iteration 3)
    *   **Description:** Define specific data structures (e.g., lists) in `config.py` for `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, `THROUGHPUT_DONE_STATUSES`, and `CFD_COLUMN_MAPPING`. Add comprehensive comments. Update `jira_connector.py` to use new config constants for default fields and page size.
    *   **Reasoning/Benefit:** Essential for making metric calculation adaptable to different Jira workflows. Decouples logic from hardcoded statuses/values.
    *   **Status:** Done (Iteration 3)
    *   **Notes:** Updated `config.py` with clearly defined, commented sections for user-configurable Jira workflow status mappings. Added `JIRA_MAX_RESULTS_PER_PAGE` and `DEFAULT_JIRA_FIELDS_TO_FETCH` constants. `jira_connector.py` updated to use these constants. Prerequisite for FEAT-005.

2.  **[Medium] [ENH-002] Implement Command-line Interface (CLI)** (Target: Iteration 5)
    *   **Description:** Use `argparse` or `typer` in `main.py` to create a user-friendly CLI for specifying JQL, projects, date ranges, output options, etc.
    *   **Reasoning/Benefit:** Improves usability and flexibility.
    *   **Status:** To Do

3.  **[Low] [ENH-003] Improve Error Handling & Logging** (Target: Iteration 5+)
    *   **Description:** Centralize logging setup. Add more detailed logging for key operations and error conditions.
    *   **Reasoning/Benefit:** Increases robustness and aids debugging.
    *   **Status:** To Do

4.  **[Medium] [ENH-004] Calculate Basic WIP (Snapshot)** (Target: Iteration 6)
    *   **Description:** Implement logic to calculate current Work In Progress based on issue statuses and configured WIP statuses in `config.py`.
    *   **Reasoning/Benefit:** Provides a key flow metric.
    *   **Status:** To Do

5.  **[Medium] [ENH-005] Generate CFD Data Points** (Target: Iteration 7)
    *   **Description:** Implement logic to generate time-series data for Cumulative Flow Diagrams using status transitions and `CFD_COLUMN_MAPPING` from `config.py`.
    *   **Reasoning/Benefit:** Enables visualization of flow, WIP, and bottlenecks.
    *   **Status:** To Do

## IV. Technical Debt & Refactoring
<!-- Tasks to improve code quality, maintainability, performance -->
1.  **[Medium] [TECH-001] Add Comprehensive Unit Tests for `data_processor.py`** (Target: Iterations 3-4)
    *   **Reason:** Ensure metric calculations in `data_processor.py` are correct and robust.
    *   **Proposed Approach:** Use `pytest`. Test with sample issue data (including `status_transitions`).
    *   **Status:** To Do

2.  **[Low] [TECH-002] Refactor API Call Logic in `jira_connector.py`** (Target: Future)
    *   **Reason:** Consolidate common API request logic.
    *   **Proposed Approach:** Create a private `_make_request` method.
    *   **Status:** Idea

## V. Documentation
<!-- Tasks related to improving project documentation -->
1.  **[Medium] [DOC-001] Detail Data Fields & Metrics in `PROJECT_METRICS_SPECIFICATIONS.md`** (Target: Iterations 2-4)
    *   **Details:** Ensure `PROJECT_METRICS_SPECIFICATIONS.md` accurately reflects all fetched fields, parsed data structures (like `status_transitions`), and how they relate to planned metrics.
    *   **Status:** To Do
    *   **Notes:** Updated for FEAT-003 & FEAT-004. Needs review after metric calculations are added.

2.  **[Medium] [DOC-002] Add Detailed Usage Instructions to `README.md`** (Target: Iteration 5)
    *   **Details:** Provide clear examples of how to run the tool via CLI (once ENH-002 is done).
    *   **Status:** To Do

3.  **[Medium] [DOC-003] Document Configuration Options (`config.py`, `.env`)** (Target: Iterations 1-3)
    *   **Details:** Ensure `README.md` and `config.py` comments clearly guide users on setting up `.env` and configuring workflow statuses in `config.py`.
    *   **Status:** Done (Iteration 3)
    *   **Notes:** `.env.example` is up-to-date. `config.py` has extensive comments for status mappings and other constants. `README.md` points to these.

## VI. Future Ideas / Wishlist
<!-- Long-term ideas not yet prioritized -->
1.  **[Idea] Integrate Kanban-specific metrics (e.g., WIP limit analysis, flow efficiency)**
2.  **[Idea] Visualize metrics/CFD directly using a plotting library (Matplotlib, Plotly, Seaborn)**
3.  **[Idea] Create a simple web UI (Streamlit/Flask) for config & results**
4.  **[Idea] Analyze issue linkage between Scrum and Kanban boards/projects**
5.  **[Idea] Add support for Story Point / Estimation analysis (e.g., Sprint Velocity stability)**
6.  **[Idea] Allow fetching data based on saved Jira Filters (by filter ID)**
7.  **[Idea] Implement caching for Jira data (e.g., file-based or in-memory) to speed up repeated runs with same parameters**
8.  **[Idea] Support different output formats (e.g., Excel with basic formatting)**
9.  **[Idea] Handle different timezones more explicitly and configurably**
10. **[Idea] Add analysis for specific issue types (e.g., Cycle Time for Bugs vs. Stories)**

---
*This document is the primary backlog. Tasks should be selected based on priority and dependencies. Ensure status and notes are updated as work progresses following the Incremental Development Workflow.*