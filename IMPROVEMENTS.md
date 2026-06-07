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
    *   **Notes/Dependencies:** Implemented Jira connection; later hardened to use email/API-token configuration via ENH-006. All unit tests pass.

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
    *   **Status:** Done (Iteration 4)
    *   **Notes/Dependencies:** Implemented `get_completion_date` and `calculate_throughput_for_period` in `src/data_processor.py`. Completion uses `resolutiondate` first, then configured done-status transitions as fallback. Unit tests cover period boundaries, status fallback, malformed dates, and invalid period inputs. FEAT-003/FEAT-004, ENH-001.

8.  **[Medium] [FEAT-008] Implement Basic Console/CSV Output** (Target: Iteration 4)
    *   **Description:** Create `src/reporting.py`. Implement functions to output summary statistics and/or raw data with calculated metrics to console or CSV.
    *   **Acceptance Criteria:** Metrics can be viewed/exported. Output is configurable.
    *   **Status:** Done (Iteration 4)
    *   **Notes/Dependencies:** Implemented console metric summary and CSV export helpers in `src/reporting.py`. Unit tests cover row flattening, missing fields, CSV output, and mixed metric availability. FEAT-005, FEAT-006, FEAT-007.

9.  **[High] [FEAT-009] Add Offline Demo Mode with Sample Jira Data** (Target: Release MVP)
    *   **Goal:** Allow the project to run end-to-end without a configured Jira server by using representative Jira-like sample issue data.
    *   **Description:** Add sample input data and a loading path that exercises existing metric calculations without requiring Jira credentials or network access.
    *   **Definition of Done:** Sample data exists in a committed non-secret location; the application can load it; cycle time, lead time, and throughput-capable completion dates can be calculated from it; documentation explains how to run the demo.
    *   **Success Criteria:** A new user can clone the repo, install dependencies, run the demo flow, and see meaningful processed metrics without creating `.env`.
    *   **How to Verify:** Run the demo command or test entry point; confirm metrics are generated from sample data; run unit tests covering sample-data loading and processing.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Added committed sample data in `sample_data/demo_issues.json`, a validated loader in `src/sample_data_loader.py`, README demo usage, metrics-spec documentation, and unit tests covering loading, validation, processing, and throughput. FEAT-005, FEAT-006. Does not depend on live Jira connectivity.

10. **[High] [FEAT-010] Generate Scrum Master Insight Summary** (Target: Release MVP)
    *   **Goal:** Convert raw issue metrics into actionable coaching insights for a Scrum Master.
    *   **Description:** Produce a concise summary including issue count, completed count, average/median cycle time, average/median lead time, throughput for a selected period, slowest items, and data-quality observations.
    *   **Definition of Done:** Insight summary logic is implemented in a reporting or analysis module; summary output is deterministic; edge cases such as no completed issues and missing metric values are handled cleanly.
    *   **Success Criteria:** The output answers "what should I look at next?" rather than only listing raw values.
    *   **How to Verify:** Run against sample data; assert expected summary values in unit tests; manually inspect console output for clarity and Scrum Master usefulness.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Added deterministic Scrum Master insight summary helpers in `src/reporting.py`, including issue counts, completed counts, average/median cycle and lead time, optional throughput, slowest cycle-time items, and data-quality observations. Unit tests cover summary calculations, missing metrics, throughput period behavior, and formatted output. FEAT-005, FEAT-006, FEAT-007, FEAT-009.

11. **[High] [FEAT-011] Add Releasable CLI Entry Point** (Target: Release MVP)
    *   **Goal:** Provide a simple command-line workflow for running demo and analysis modes.
    *   **Description:** Add `main.py` or an equivalent entry point with commands for offline demo analysis and file-based analysis.
    *   **Definition of Done:** Users can run clear commands such as demo mode and input-file analysis; invalid arguments produce helpful messages; the CLI does not require Jira credentials for offline/demo paths.
    *   **Success Criteria:** A non-developer user can follow README instructions and run the MVP workflow without editing Python files.
    *   **How to Verify:** Run CLI help; run demo mode; run analysis against sample data; add tests for argument parsing or command orchestration where practical.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Added `main.py` with `demo` and `analyze-file` commands. Demo mode runs without `.env`, applies sample workflow status mappings, processes committed sample data, and prints the Scrum Master insight summary with throughput. File analysis accepts Jira-like JSON and optional throughput period arguments. Unit tests cover help, demo output, file analysis, invalid files, and incomplete period arguments. FEAT-009, FEAT-010.

12. **[High] [FEAT-012] Add Data Quality Checks and Warnings** (Target: Release MVP)
    *   **Goal:** Surface Jira data gaps and workflow mapping issues as useful insights, not silent failures.
    *   **Description:** Detect missing resolution dates, missing cycle start/end transitions, invalid timestamps, empty status configuration, and dates that are logically inconsistent.
    *   **Definition of Done:** Data quality checks are implemented with structured warning records or clear report fields; checks are included in the insight summary; tests cover common failure modes.
    *   **Success Criteria:** Users can distinguish "metric is slow" from "metric could not be calculated because data/configuration is incomplete."
    *   **How to Verify:** Run against sample data containing known gaps; confirm warnings appear; run tests for each warning category.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Added structured per-issue data-quality warning records in `src/data_processor.py` and grouped warning observations in Scrum Master insight summaries. Warnings cover missing resolution dates, missing cycle start/end transitions, invalid created/resolution/transition timestamps, empty cycle/throughput status mappings, and resolution-before-created inconsistencies. Unit tests cover warning generation and summary grouping. FEAT-005, FEAT-006, FEAT-009, FEAT-010.

13. **[High] [FEAT-013] Create Releasable MVP Report Format** (Target: Release MVP)
    *   **Goal:** Package the most valuable insights into one polished output suitable for repeated Scrum Master use.
    *   **Description:** Produce a stable report format that combines summary metrics, top bottleneck candidates, data-quality warnings, and optional CSV/JSON export of processed issue details.
    *   **Definition of Done:** Report output has a predictable structure; CSV/JSON export includes key issue fields and calculated metrics; README documents output fields and usage.
    *   **Success Criteria:** The report is useful for reviewing team flow in a coaching conversation without needing to inspect raw Jira JSON.
    *   **How to Verify:** Run report generation from sample data; inspect exported file contents; run tests for report formatting and exported fields.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Added a stable MVP report payload in `src/reporting.py` combining summary metrics, bottleneck candidates, grouped data-quality warnings, and issue detail rows. CSV issue exports now include data-quality warning counts/codes, and JSON report export is available through `write_report_json`. CLI `demo` and `analyze-file` commands now support `--csv-output` and `--json-output`. Unit tests cover report structure, formatting, JSON export, CSV warning fields, and CLI export arguments. FEAT-008, FEAT-010, FEAT-012.

## III. Enhancements & Refinements
<!-- Improvements to existing features, usability, performance -->
1.  **[High] [ENH-001] Add Configuration for Cycle/Lead Time Statuses in `config.py`** (Target: Iteration 3)
    *   **Status:** Done (Iteration 3)
    *   **Notes:** `config.py` has user-configurable status mappings and constants. Prerequisite for FEAT-005.

2.  **[Medium] [ENH-002] Implement Command-line Interface (CLI)** (Target: Iteration 5)
    *   **Status:** Done (Release MVP via FEAT-011)
    *   **Notes:** Covered by FEAT-011. `main.py` now provides offline demo and file-based analysis CLI workflows with optional CSV/JSON exports.

3.  **[Low] [ENH-003] Improve Error Handling & Logging** (Target: Iteration 5+)
    *   **Status:** To Do

4.  **[Medium] [ENH-004] Calculate Basic WIP (Snapshot)** (Target: Iteration 6)
    *   **Status:** Done (Iteration 6)
    *   **Notes:** Added `WIP_STATUSES` configuration, `calculate_wip_snapshot` in `src/data_processor.py`, WIP output in Scrum Master summaries and MVP report JSON, demo workflow WIP mappings, and unit tests for processing/reporting behavior.

5.  **[Medium] [ENH-005] Generate CFD Data Points** (Target: Iteration 7)
    *   **Status:** To Do

6.  **[Medium] [ENH-006] Align Authentication Configuration with Jira API Token Guidance** (Target: Post-MVP Hardening)
    *   **Goal:** Resolve the current mismatch between API-token guidance and Basic Auth/password implementation.
    *   **Description:** Decide and implement the preferred authentication strategy for Jira Cloud/Server, update `.env.example`, code, tests, and documentation consistently.
    *   **Definition of Done:** Credential variable names and authentication behavior are consistent across code, tests, README, `.env.example`, and project guidance.
    *   **Success Criteria:** Users know exactly which Jira credential to create and where to configure it.
    *   **How to Verify:** Run authentication unit tests; inspect README and `.env.example`; optionally verify with a real Jira instance when available.
    *   **Status:** Done (Post-MVP Hardening)
    *   **Notes/Dependencies:** Aligned `src/jira_connector.py`, `.env.example`, README, metric specs, and connector tests around `JIRA_API_TOKEN`. Jira requests continue to use Jira-compatible email/API-token authentication. Verified with mocked request tests; optional live Jira verification still depends on user credentials.

7.  **[Medium] [ENH-007] Remove Import-Time Diagnostic Noise** (Target: Release MVP)
    *   **Goal:** Make command output professional and focused on useful insights.
    *   **Description:** Replace import-time `print` diagnostics in configuration, connector, and test setup with proper logging or remove them where no longer needed.
    *   **Definition of Done:** Importing modules does not print debug text; tests still pass; logging remains available for actual runtime errors and diagnostics.
    *   **Success Criteria:** Running the CLI or tests produces readable output without unrelated import-path messages.
    *   **How to Verify:** Run tests and demo command; confirm output contains only relevant logs/report content.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** Removed import-time diagnostic prints from `config.py`, `src/jira_connector.py`, and `tests/conftest.py`; replaced useful connector diagnostics with debug logging; stopped `src/data_processor.py` from installing a debug stream handler at import time; removed test debug prints. CLI demo output is now focused on report content. Supports release polish; no Jira server needed.

## IV. Technical Debt & Refactoring
<!-- Tasks to improve code quality, maintainability, performance -->
1.  **[Medium] [TECH-001] Add Comprehensive Unit Tests for `data_processor.py`** (Target: Iterations 3-4)
    *   **Status:** In Progress
    *   **Notes:** Tests for Cycle Time (FEAT-005), Lead Time (FEAT-006), and Throughput (FEAT-007) added. Additional coverage may still be needed as new processing features are introduced.

2.  **[Low] [TECH-002] Refactor API Call Logic in `jira_connector.py`** (Target: Future)
    *   **Status:** Idea

3.  **[Medium] [TECH-003] Reconcile Throughput Implementation with Backlog and Metric Specs** (Target: Release MVP)
    *   **Goal:** Resolve documentation drift where throughput logic and tests exist but FEAT-007 and metric specs still describe throughput as planned.
    *   **Description:** Review current throughput code for completeness, fill any gaps, then update task status and metric documentation accordingly.
    *   **Definition of Done:** Throughput implementation, tests, README, `PROJECT_METRICS_SPECIFICATIONS.md`, and `IMPROVEMENTS.md` all describe the same behavior.
    *   **Success Criteria:** A future contributor can understand whether throughput is complete, partial, or pending without reading every source file.
    *   **How to Verify:** Run throughput tests; inspect documentation for consistency; confirm FEAT-007 status is accurate.
    *   **Status:** Done (Release MVP documentation alignment)
    *   **Notes/Dependencies:** Reconciled throughput implementation, tests, README, `PROJECT_METRICS_SPECIFICATIONS.md`, `config.py` comments, and FEAT-007 backlog status. FEAT-007.

## V. Documentation
<!-- Tasks related to improving project documentation -->
1.  **[Medium] [DOC-001] Detail Data Fields & Metrics in `PROJECT_METRICS_SPECIFICATIONS.md`** (Target: Iterations 2-4)
    *   **Status:** In Progress
    *   **Notes:** Updated for FEAT-003, FEAT-004, ENH-001, FEAT-005, FEAT-006, and FEAT-007. Needs ongoing review as additional metrics are added.

2.  **[Medium] [DOC-002] Add Detailed Usage Instructions to `README.md`** (Target: Iteration 5)
    *   **Status:** Done (Release MVP)
    *   **Notes:** README now includes install steps, offline demo usage, file analysis, CSV/JSON export commands, output field descriptions, verification commands, and troubleshooting guidance.

3.  **[Medium] [DOC-003] Document Configuration Options (`config.py`, `.env`)** (Target: Iterations 1-3)
    *   **Status:** Done (Iteration 3)

4.  **[High] [DOC-004] Document Offline MVP Usage and Release Workflow** (Target: Release MVP)
    *   **Goal:** Make the project understandable and runnable without Jira configuration.
    *   **Description:** Update README and related docs with offline demo instructions, sample data expectations, report output descriptions, and verification commands.
    *   **Definition of Done:** README includes install, demo, analyze, test, and troubleshooting sections for the releasable MVP; docs clearly explain when `.env` is needed and when it is not.
    *   **Success Criteria:** A new user can run the project and understand the output using only the documentation.
    *   **How to Verify:** Follow README from a clean checkout; run the documented demo path; confirm all referenced files and commands exist.
    *   **Status:** Done (Release MVP)
    *   **Notes/Dependencies:** README now documents offline setup, demo mode, file-based analysis, report exports, output fields, verification commands, and troubleshooting. Verified documented commands after update. FEAT-009, FEAT-011, FEAT-013.

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
