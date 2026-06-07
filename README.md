# Jira Insights

<!-- One-liner description of the project -->
A Python tool to fetch and analyze Jira data for Scrum Masters to gain insights into team performance, project health, and process bottlenecks across multiple teams.

## 1. Overview
<!-- Expand slightly on the project's purpose and what it does. Reference PROJECT_PURPOSE.md -->
**Jira Insights** is a Python application designed to **automate the collection and analysis of data from Jira projects and boards**. It connects to Jira using an email address and API token, fetches ticket information (including status transition history), and calculates key agile metrics like **Cycle Time**, **Lead Time**, and **Throughput**. User-specific workflow configurations in `config.py` are essential for accurate metric calculation. Future enhancements will include WIP analysis and more.

For a detailed understanding of the project's goals, scope, and philosophy, please see `PROJECT_PURPOSE.md`.

## 2. Features (Current / Planned for MVP)
<!-- List key features. Align with "In Scope" from PROJECT_PURPOSE.md -->
*   **Jira Connectivity:** Connects to Jira using an email address and API token from `.env`.
*   **Data Fetching:**
    *   Retrieves issue data (default fields in `config.py`; others specifiable) via JQL, with pagination.
    *   Fetches and parses issue **changelog** for a sorted list of status transitions.
*   **Offline Demo Data:** Loads committed Jira-like sample issues without Jira credentials, useful for first-run validation and tests.
*   **Configurable Workflow Statuses:** User-defined mappings in `config.py` for `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, etc.
*   **Cycle Time Calculation:** Calculates cycle time based on status transitions and configured workflow statuses. Output unit configurable (default: days).
*   **Lead Time Calculation:** Calculates lead time (creation to resolution) using fetched date fields. Output unit configurable (default: days).
*   **Throughput Calculation:** Counts completed issues for a timezone-aware reporting period using `resolutiondate` first, then configured done-status transitions as fallback.
*   **WIP Snapshot:** Counts currently active issues using configured WIP statuses.
*   **Data Quality Warnings:** Flags missing resolution dates, incomplete cycle transitions, invalid timestamps, empty status mappings, and inconsistent dates.
*   **Basic Data Output:** Formats processed issue metrics for console summaries and CSV export.
*   **Scrum Master Insight Summary:** Produces deterministic coaching-oriented summaries with average/median flow metrics, throughput, slowest items, and data-quality observations.
*   **MVP Report Export:** Packages summary metrics, bottleneck candidates, data-quality warnings, and issue details into stable CSV/JSON outputs.
*   **CLI Workflows:** Runs offline demo and file-based analysis commands without requiring Jira credentials.
*   **Configurable Scope (Planned).**

## 3. Core Building Blocks & Architecture (High-Level)
<!-- Describe the main components and how they fit together. This will evolve. -->
*   **Input:** Jira REST API, committed sample data, `config.py`, `.env`.
*   **Processing:**
    *   `src/jira_connector.py`: Handles authentication, API calls, status transition parsing.
    *   `src/sample_data_loader.py`: Loads offline demo issue data from JSON.
    *   `src/data_processor.py`: Contains logic for metric calculations (Cycle Time, Lead Time, Throughput) and structured data-quality warnings.
    *   `src/reporting.py`: Builds console summaries and CSV exports from processed issue metrics.
    *   `main.py`: Orchestrates offline demo and file-based CLI workflows.
*   **Output:** Console summaries, List of Dictionaries (issues with metrics), CSV issue exports, JSON MVP reports.
*   **Configuration:** `.env` for secrets; `config.py` for API paths, defaults, and **user-defined Jira workflow status mappings**.
*   **Key Technologies:** Python, `requests`, `python-dotenv`, `pytest`, `requests-mock`. `pandas` planned.

## 4. Getting Started

### Prerequisites
*   Python 3.9+
*   `pip`, `virtualenv`
*   Jira access and an API token only for live Jira API experiments. The offline MVP does not require Jira credentials.

### Installation
1.  Clone repository.
2.  Set up and activate a virtual environment.
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Optional for live Jira API experiments: set up `.env` by copying `.env.example`.
    ```dotenv
    JIRA_URL=https://your-domain.atlassian.net
    JIRA_EMAIL=your-email@example.com
    JIRA_API_TOKEN=your_actual_jira_api_token_here
    ```
5.  Configure workflow statuses for file-based analysis:
    *   Edit `config.py`.
    *   Update `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, `THROUGHPUT_DONE_STATUSES`, and `WIP_STATUSES` lists.
    *   The `demo` command applies demo-specific mappings internally.

### Quick Offline MVP Run
No `.env`, Jira access, or network connection is required.

```bash
python3 main.py --help
python3 main.py demo
```

The demo command loads `sample_data/demo_issues.json`, applies sample workflow status mappings, calculates metrics, and prints a Scrum Master insight summary.

### Analyze a Jira-Like JSON File
Use `analyze-file` when you have local Jira-like issue JSON in the same shape as the demo file.

```bash
python3 main.py analyze-file sample_data/demo_issues.json --period-start 2024-03-01 --period-end 2024-03-12
```

The reporting period is optional, but both `--period-start` and `--period-end` must be provided together when you want throughput in the summary. Period boundaries are timezone-aware internally; date-only values are treated as UTC.

Unlike `demo`, `analyze-file` uses the workflow mappings currently set in `config.py`. If those lists are empty, the report will still run and will include data-quality warnings explaining which metrics could not be calculated.

### Export the MVP Report
Use `--csv-output` for flat issue-level details and `--json-output` for the full MVP report payload.

```bash
python3 main.py demo --csv-output demo_details.csv --json-output demo_report.json
python3 main.py analyze-file sample_data/demo_issues.json --period-start 2024-03-01 --period-end 2024-03-12 --csv-output issue_details.csv --json-output mvp_report.json
```

### Understand the Output
Console summary:
*   `Issues analyzed`: Total issues loaded from the input file.
*   `Completed issues`: Issues with a completion date from `resolutiondate` or done-status transition fallback.
*   `WIP snapshot`: Issues whose current Jira status is configured as active work.
*   `Cycle time`: Average and median active flow time.
*   `Lead time`: Average and median time from creation to resolution.
*   `Throughput in selected period`: Count of issues completed in the supplied reporting period.
*   `Slowest cycle-time items`: Bottleneck candidates for Scrum Master inspection.
*   `Data quality observations`: Warnings that explain missing or unreliable metrics.

CSV export fields:
*   Issue identity and context: `key`, `summary`, `issue_type`, `status`, `project_key`.
*   Raw dates: `created`, `resolutiondate`.
*   Metrics: `cycle_time`, `cycle_time_unit`, `lead_time`, `lead_time_unit`.
*   Data quality: `data_quality_warning_count`, `data_quality_warning_codes`.

JSON report sections:
*   `summary`: Scrum Master insight summary.
*   `bottleneck_candidates`: Slowest cycle-time items.
*   `data_quality`: Grouped observations and warning counts by code.
*   `issue_details`: Flat issue rows matching the CSV structure.

### Verify the MVP Workflow
Run these commands from the project root:

```bash
python3 main.py --help
python3 main.py demo
python3 main.py analyze-file sample_data/demo_issues.json --period-start 2024-03-01 --period-end 2024-03-12
python3 main.py demo --csv-output /tmp/jira_insights_demo_details.csv --json-output /tmp/jira_insights_demo_report.json
python3 -m pytest
```

### Reporting Processed Metrics
Reporting helpers can also be called from Python after issues have been processed:
```python
from src.reporting import print_metric_summary, write_metrics_csv

print_metric_summary(processed_issues)
write_metrics_csv(processed_issues)
```

CSV export defaults to `config.DEFAULT_OUTPUT_FILENAME` unless an explicit path is provided.

### Generating Scrum Master Insights
Use `print_insight_summary` for a coaching-oriented report that highlights completed issue count, average and median cycle/lead time, optional throughput, slowest cycle-time items, and data-quality observations. These observations help distinguish slow flow from incomplete Jira data or workflow configuration gaps.

```python
from datetime import datetime, timezone

from src.reporting import build_insight_summary, print_insight_summary

summary = build_insight_summary(
    processed_issues,
    throughput_period_start=datetime(2024, 3, 1, tzinfo=timezone.utc),
    throughput_period_end=datetime(2024, 3, 12, tzinfo=timezone.utc),
)
print_insight_summary(
    processed_issues,
    throughput_period_start=datetime(2024, 3, 1, tzinfo=timezone.utc),
    throughput_period_end=datetime(2024, 3, 12, tzinfo=timezone.utc),
)
```

### Running Tests
```bash
python3 -m pytest
```

### Troubleshooting
*   `Sample data file not found`: Confirm the input path exists and run commands from the project root.
*   `Sample data file is not valid JSON`: Validate that the file is a JSON list of Jira issue objects.
*   Missing cycle time: Check `config.CYCLE_START_STATUSES`, `config.CYCLE_END_STATUSES`, and issue `status_transitions`.
*   Missing throughput from status fallback: Check `config.THROUGHPUT_DONE_STATUSES` or provide `resolutiondate`.
*   Unexpected WIP count: Check `config.WIP_STATUSES` against current Jira status names.
*   Need diagnostics: enable Python logging in your calling code or test harness to inspect connector and processing details.
*   `python: command not found`: Use `python3` on systems where `python` is not installed.

## 5. Development Workflow & Contribution Guidelines

Use small, tested, documented changes. Keep code, tests, and project documentation synchronized through each increment, with `IMPROVEMENTS.md` acting as the product backlog.

Key Guidelines: PEP 8, clarity, modularity, configuration-driven behavior, and tested business logic.

## 6. Project Structure (High-Level)
```
jira-insights/
├── .env, .env.example, .gitignore
├── config.py           # Configs, STATUS MAPPINGS
├── main.py
├── sample_data/
│   └── demo_issues.json # Offline Jira-like demo data
├── src/
│   ├── __init__.py
│   ├── jira_connector.py # API interaction, changelog parsing
│   ├── sample_data_loader.py # Offline demo data loading
│   ├── data_processor.py # Cycle/Lead Time & other metric calculations
│   └── reporting.py      # Console and CSV metric output
├── tests/
│   ├── __init__.py, conftest.py
│   ├── test_data_processor.py
│   ├── test_jira_connector.py
│   ├── test_reporting.py
│   └── test_sample_data_loader.py
├── requirements.txt
├── PROJECT_PURPOSE.md, README.md, PROJECT_METRICS_SPECIFICATIONS.md
├── IMPROVEMENTS.md
```

## 7. Key Technologies

*   Python 3.9+, `python-dotenv`, `requests`
*   Testing: `pytest`, `requests-mock`
*   Data Processing (planned): `pandas`

## 8. Future Roadmap (High-Level)

*   Live Jira analysis command.
*   See `IMPROVEMENTS.md`.

## 9. Disclaimer

Accuracy depends on Jira data and `config.py` status mappings.
**Security Note:** Protect `.env`. Jira API tokens should be treated like passwords and rotated if exposed.
