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
    *   **Status:** Done (Iteration 1)
    *   **Notes/Dependencies:** Initial project structure, configuration templates, `.gitignore`, and documentation files created.

2.  **[High] [FEAT-002] Implement Jira Connection & Authentication** (Target: Iteration 1)
    *   **Status:** Done (Iteration 1)
    *   **Notes/Dependencies:** Implemented Jira connection using Basic Authentication. All unit tests pass.

3.  **[High] [FEAT-003] Fetch Basic Issue Data via JQL** (Target: Iteration 2)
    *   **Status:** Done (Iteration 2)
    *   **Notes/Dependencies:** Implemented JQL issue fetching with pagination and field selection. All unit tests pass. FEAT-002.

4.  **[High] [FEAT-004] Fetch Issue Changelog (Status Transitions)** (Target: Iteration 2)
    *   **Status:** Done (Iteration 2)
    *   **Notes/Dependencies:** Added changelog fetching and parsing for status transitions. All unit tests pass. FEAT-003.

5.  **[High] [FEAT-005] Implement Cycle Time Calculation** (Target: Iteration 3)
    *   **Status:** Done (Iteration 3)
    *   **Notes/Dependencies:** Implemented 'calculate_cycle_time' in `src/data_processor.py` using status transitions and configured statuses. All unit tests pass. FEAT-004, ENH-001.

6.  **[High] [FEAT-006] Implement Lead Time Calculation** (Target: Iteration 3)
    *   **Description:** Implement logic in `src/data_processor.py` to calculate lead time for each issue using the `fields.created` and `fields.resolutiondate` fields.
    *   **Acceptance Criteria:** Lead time is calculated correctly. Handles missing `resolutiondate`. Unit tests pass.
    *   **Status:** Done (Iteration 3)
    *   **Notes/Dependencies:** Implemented 'calculate_lead_time' in `src/data_processor.py` using 'created' and 'resolutiondate' fields. 'process_issues_for_metrics' updated to include lead time. All unit tests pass. FEAT-003.

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
    *   **Status:** Done (Iteration 3)
    *   **Notes:** `config.py` has user-configurable status mappings and constants. Prerequisite for FEAT-005.

2.  **[Medium] [ENH-002] Implement Command-line Interface (CLI)** (Target: Iteration 5)
    *   **Status:** To Do

3.  **[Low] [ENH-003] Improve Error Handling & Logging** (Target: Iteration 5+)
    *   **Status:** To Do

4.  **[Medium] [ENH-004] Calculate Basic WIP (Snapshot)** (Target: Iteration 6)
    *   **Status:** To Do

5.  **[Medium] [ENH-005] Generate CFD Data Points** (Target: Iteration 7)
    *   **Status:** To Do

## IV. Technical Debt & Refactoring
<!-- Tasks to improve code quality, maintainability, performance -->
1.  **[Medium] [TECH-001] Add Comprehensive Unit Tests for `data_processor.py`** (Target: Iterations 3-4)
    *   **Status:** In Progress
    *   **Notes:** Tests for Cycle Time (FEAT-005) and Lead Time (FEAT-006) added. Need tests for Throughput (FEAT-007).

2.  **[Low] [TECH-002] Refactor API Call Logic in `jira_connector.py`** (Target: Future)
    *   **Status:** Idea

## V. Documentation
<!-- Tasks related to improving project documentation -->
1.  **[Medium] [DOC-001] Detail Data Fields & Metrics in `PROJECT_METRICS_SPECIFICATIONS.md`** (Target: Iterations 2-4)
    *   **Status:** In Progress
    *   **Notes:** Updated for FEAT-003, FEAT-004, ENH-001, FEAT-005, FEAT-006. Needs ongoing review.

2.  **[Medium] [DOC-002] Add Detailed Usage Instructions to `README.md`** (Target: Iteration 5)
    *   **Status:** To Do

3.  **[Medium] [DOC-003] Document Configuration Options (`config.py`, `.env`)** (Target: Iterations 1-3)
    *   **Status:** Done (Iteration 3)

## VI. Future Ideas / Wishlist
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