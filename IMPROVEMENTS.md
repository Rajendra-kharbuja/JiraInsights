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
    *   **Acceptance Criteria:** Project can be cloned, basic structure exists, documentation templates are present. `requirements.txt` includes initial libraries (`python-dotenv`, `requests`, `pandas`, `pytest`).
    *   **Status:** To Do
    *   **Notes/Dependencies:** Foundational first step.

2.  **[High] [FEAT-002] Implement Jira Connection & Authentication** (Target: Iteration 1)
    *   **Description:** Create `src/jira_connector.py`. Implement a function/class that reads Jira URL, email, and API token from `.env` variables. Include a method to test the connection (e.g., by making a simple API call like `/rest/api/3/myself`). Handle basic connection errors gracefully (e.g., incorrect URL, invalid credentials).
    *   **Acceptance Criteria:** Can successfully authenticate against a Jira instance using credentials from `.env`. Returns a clear success/failure indication. Logs informative errors on failure.
    *   **Status:** To Do
    *   **Notes/Dependencies:** Requires `.env` setup by the user. Needs basic unit tests (potentially mocking the API call).

3.  **[High] [FEAT-003] Fetch Basic Issue Data via JQL** (Target: Iteration 2)
    *   **Description:** Extend `src/jira_connector.py`. Add a function that accepts a JQL string and fetches issues using the Jira search API (`/rest/api/3/search`). Initially fetch key fields required for Lead Time and Throughput (`id`, `key`, `fields.issuetype`, `fields.status`, `fields.created`, `fields.resolutiondate`). Implement handling for API pagination (`startAt`, `maxResults`) to retrieve all matching issues.
    *   **Acceptance Criteria:** Can retrieve a list of issues matching a provided JQL query. Pagination correctly fetches all results. Returns structured data (e.g., list of dicts or ideally a pandas DataFrame). Handles potential API errors during search.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-002. The JQL query itself will likely be constructed in `main.py` based on config/args.

4.  **[High] [FEAT-004] Fetch Issue Changelog (Status Transitions)** (Target: Iteration 2)
    *   **Description:** Modify the issue fetching function (FEAT-003) in `src/jira_connector.py` to include the `changelog` in the `expand` parameter of the search API call. Add parsing logic (potentially in `data_processor.py` or a helper function) to extract relevant status transitions (timestamp, fromStatus, toStatus) from the nested changelog data for each issue.
    *   **Acceptance Criteria:** Fetched issue data (e.g., DataFrame) includes easily accessible status transition history for each issue.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-003. Increases API response size and parsing complexity. Crucial for Cycle Time.

5.  **[High] [FEAT-005] Implement Cycle Time Calculation** (Target: Iteration 3)
    *   **Description:** Create `src/data_processor.py`. Implement logic to calculate cycle time for each completed issue. This function will take the fetched issue data (including parsed status transitions from FEAT-004) and configurable 'Cycle Start'/'Cycle End' statuses (defined in `config.py`). It needs to find the first entry into 'Start' and the first entry into 'End' *after* the start timestamp.
    *   **Acceptance Criteria:** Cycle time is calculated correctly based on transition history and `config.py` statuses. Handles issues with multiple entries/exits from statuses correctly. Returns cycle time (e.g., in days or hours) or NaN/None if calculation isn't possible. Requires unit tests with sample data.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-004, ENH-001 (Config for statuses).

6.  **[High] [FEAT-006] Implement Lead Time Calculation** (Target: Iteration 3)
    *   **Description:** Implement logic in `src/data_processor.py` to calculate lead time for each issue using the `fields.created` and `fields.resolutiondate` fields obtained in FEAT-003.
    *   **Acceptance Criteria:** Lead time is calculated correctly (e.g., in days or hours). Handles missing `resolutiondate` (returns NaN/None). Requires unit tests.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-003.

7.  **[Medium] [FEAT-007] Implement Throughput Calculation** (Target: Iteration 4)
    *   **Description:** Implement logic (likely in `data_processor.py` or `src/reporting.py`) to calculate throughput. This involves counting the number of issues resolved (based on `resolutiondate` or entering a final status from changelog) within specific time periods (e.g., weekly, monthly). The period should be configurable or determined by reporting needs.
    *   **Acceptance Criteria:** Throughput count is calculated correctly for given time windows (e.g., produces a count per week for the last N weeks). Requires unit tests.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-003/FEAT-004.

8.  **[Medium] [FEAT-008] Implement Basic Console/CSV Output** (Target: Iteration 4)
    *   **Description:** Create `src/reporting.py`. Implement functions to take the processed data (DataFrame with calculated metrics) and output summary statistics (e.g., Avg/Median Cycle/Lead Time, Weekly Throughput) to the console in a readable format. Also, add an option to save the raw data with calculated metrics per issue to a CSV file.
    *   **Acceptance Criteria:** Calculated metrics can be viewed on the console. Data per issue can be exported to CSV. Output filename should be configurable.
    *   **Status:** To Do
    *   **Notes/Dependencies:** FEAT-005, FEAT-006, FEAT-007.

## III. Enhancements & Refinements
<!-- Improvements to existing features, usability, performance -->
1.  **[High] [ENH-001] Add Configuration for Cycle/Lead Time Statuses in `config.py`** (Target: Iteration 3)
    *   **Description:** Define specific data structures (e.g., lists or dicts) in `config.py` to hold the Jira status names that correspond to 'Cycle Start', 'Cycle End', and potentially 'Final/Done' (for Throughput if `resolutiondate` isn't used). Ensure `data_processor.py` reads and uses these configurations. Add clear comments explaining these settings.
    *   **Reasoning/Benefit:** Essential for making metric calculation adaptable to different Jira workflows. Decouples logic from hardcoded statuses.
    *   **Status:** To Do
    *   **Notes:** Prerequisite for FEAT-005.

2.  **[Medium] [ENH-002] Implement Command-line Interface (CLI)** (Target: Iteration 5)
    *   **Description:** Use `argparse` or `typer` in `main.py` to create a user-friendly CLI. Allow users to specify parameters like Jira project keys (`--projects`), board IDs (`--boards`), JQL filter (`--jql`), date ranges (`--start-date`, `--end-date`), output file path (`--output`), and output format (`--format CSV`).
    *   **Reasoning/Benefit:** Makes the tool much easier and more flexible to run without modifying code or config files for every execution.
    *   **Status:** To Do

3.  **[Low] [ENH-003] Improve Error Handling & Logging** (Target: Iteration 5+)
    *   **Description:** Enhance error handling in `jira_connector.py` for API issues (timeouts, rate limits, specific 4xx/5xx errors). Add more informative logging using the `logging` module throughout the application (e.g., stages of execution, number of issues fetched, errors encountered). Configure basic logging setup (level, format, output to console/file).
    *   **Reasoning/Benefit:** Increases tool robustness, reliability, and makes debugging easier.
    *   **Status:** To Do

4.  **[Medium] [ENH-004] Calculate Basic WIP (Snapshot)** (Target: Iteration 6)
    *   **Description:** Implement logic to calculate the number of items currently in progress. Requires fetching issues matching a WIP JQL (e.g., `status in ('In Progress', 'Code Review')`) or filtering the main dataset based on current status and configured WIP statuses from `config.py`.
    *   **Reasoning/Benefit:** Provides a key flow metric often monitored by teams.
    *   **Status:** To Do

5.  **[Medium] [ENH-005] Generate CFD Data Points** (Target: Iteration 7)
    *   **Description:** Implement logic to generate the time-series data needed for a CFD. Requires mapping Jira statuses to CFD columns (in `config.py`) and processing the status transition history to count issues in each column state for each day in a specified date range. Output as CSV/JSON.
    *   **Reasoning/Benefit:** Enables visualization of flow, WIP, and bottlenecks over time using external tools (like spreadsheet software or plotting libraries).
    *   **Status:** To Do

## IV. Technical Debt & Refactoring
<!-- Tasks to improve code quality, maintainability, performance -->
1.  **[Medium] [TECH-001] Add Comprehensive Unit Tests** (Target: Iterations 2-4)
    *   **Reason:** Ensure core logic, especially metric calculations in `data_processor.py` and parsing in `jira_connector.py`, is correct and robust against edge cases. Facilitates safer refactoring later.
    *   **Proposed Approach:** Use `pytest`. Create test cases with sample input data (mock Jira responses using `requests-mock`, sample DataFrames). Test metric calculations, status parsing, date handling, error conditions. Aim for good coverage of `data_processor.py`.
    *   **Status:** To Do

2.  **[Low] [TECH-002] Refactor API Call Logic** (Target: Future)
    *   **Reason:** Consolidate API call logic (handling auth, base URL, error checking, retries if added) into a reusable helper function or class method within `jira_connector.py` to avoid repetition as more endpoints are used.
    *   **Proposed Approach:** Create a private `_make_request` method handling common request logic.
    *   **Status:** Idea

## V. Documentation
<!-- Tasks related to improving project documentation -->
1.  **[Medium] [DOC-001] Detail Data Fields & Metrics in `PROJECT_METRICS_SPECIFICATIONS.md`** (Target: Iterations 2-4)
    *   **Details:** As data fetching (FEAT-003, FEAT-004) and metric calculation (FEAT-005, FEAT-006, FEAT-007) are implemented, accurately document the specific Jira fields being used, how metrics are calculated, and required configurations in `PROJECT_METRICS_SPECIFICATIONS.md`. Ensure it stays synchronized with code and `config.py`.
    *   **Status:** To Do

2.  **[Medium] [DOC-002] Add Detailed Usage Instructions to `README.md`** (Target: Iteration 5)
    *   **Details:** Once the CLI (ENH-002) is implemented, provide clear examples in `README.md` showing how to run the tool with different options (projects, dates, output). Explain the output formats.
    *   **Status:** To Do

3.  **[Medium] [DOC-003] Document Configuration Options (`config.py`, `.env`)** (Target: Iterations 1-3)
    *   **Details:** Clearly document all required variables in `.env.example`. Add comprehensive comments in `config.py` explaining each setting, its purpose, and expected format (especially for status mappings). Ensure `README.md` points users to these files for configuration.
    *   **Status:** To Do

## VI. Future Ideas / Wishlist
<!-- Long-term ideas not yet prioritized -->
1.  **[Idea] Integrate Kanban-specific metrics (e.g., WIP limit analysis, flow efficiency)**
2.  **[Idea] Visualize metrics/CFD directly using a plotting library (Matplotlib, Plotly, Seaborn)**
3.  **[Idea] Create a simple web UI (Streamlit/Flask) for config & results**
4.  **[Idea] Analyze issue linkage between different boards/projects**
5.  **[Idea] Add support for Story Point / Estimation analysis (e.g., Sprint Velocity stability)**
6.  **[Idea] Allow fetching data based on saved Jira Filters (by filter ID)**
7.  **[Idea] Implement caching for Jira data (e.g., file-based or in-memory) to speed up repeated runs with same parameters**
8.  **[Idea] Support different output formats (e.g., Excel with basic formatting)**
9.  **[Idea] Handle different timezones more explicitly and configurably**
10. **[Idea] Add analysis for specific issue types (e.g., Cycle Time for Bugs vs. Stories)**

---
*This document is the primary backlog. Tasks should be selected based on priority and dependencies. Ensure status and notes are updated as work progresses following the Incremental Development Workflow.*