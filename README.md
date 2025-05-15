# Jira Insights

<!-- One-liner description of the project -->
A Python tool to fetch and analyze Jira data for Scrum Masters to gain insights into team performance, project health, and process bottlenecks across multiple teams.

## 1. Overview
<!-- Expand slightly on the project's purpose and what it does. Reference PROJECT_PURPOSE.md -->
**Jira Insights** is a Python application designed to **automate the collection and analysis of data from Jira projects and boards**. It addresses the challenge faced by Scrum Masters managing multiple teams by connecting to the Jira API using Basic Authentication, fetching relevant ticket information (including ID, key, type, status, created/resolved dates, and issue changelog for status transition history) via JQL with pagination. Configurations for workflow statuses crucial for these metrics are managed in `config.py`.

For a detailed understanding of the project's goals, scope, and philosophy, please see `PROJECT_PURPOSE.md`.

## 2. Features (Current / Planned for MVP)
<!-- List key features. Align with "In Scope" from PROJECT_PURPOSE.md -->
*   **Jira Connectivity:** Securely connect to Jira Cloud or Server using Jira Basic Authentication (Email/Password loaded from `.env`).
*   **Data Fetching:**
    *   Retrieve essential issue data (default fields defined in `config.py`; other fields specifiable) from Jira via JQL queries, with robust pagination handling.
    *   Fetch issue **changelog** and parse it to extract a chronologically sorted list of status transitions for each issue (stored under `status_transitions` key).
*   **Configurable Workflow Statuses:** User-defined mappings in `config.py` for `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, and `THROUGHPUT_DONE_STATUSES` to tailor metric calculations to specific Jira workflows.
*   **Configurable Scope (Planned):** Specify target Jira projects and/or boards.
*   **Cycle Time Calculation (Planned):** Using parsed `status_transitions` and configured statuses.
*   **Lead Time Calculation (Planned):** Using fetched date fields.
*   **Throughput Calculation (Planned):** Using fetched dates or configured 'done' statuses.
*   **Basic Data Output (Planned).**

## 3. Core Building Blocks & Architecture (High-Level)
<!-- Describe the main components and how they fit together. This will evolve. -->
*   **Input:** Jira REST API, Configuration files (`config.py`, `.env`), Command-line arguments (planned).
*   **Processing:**
    *   `src/jira_connector.py`: Handles authentication, API calls (fetching issues, changelogs), and parsing of status transitions.
    *   `src/data_processor.py` (Planned): Calculates metrics using fetched data and `config.py` status mappings.
    *   `src/reporting.py` (Planned): Formats and outputs results.
    *   `main.py`: Main script orchestrating the workflow.
*   **Output:** Console logs, List of Dictionaries (from fetch function, including `status_transitions`), CSV/JSON files (planned).
*   **Configuration:**
    *   `.env`: For sensitive credentials (Jira URL, Email, Password).
    *   `config.py`: For non-sensitive settings, API paths, default fetch fields, page size, and **crucially, user-defined Jira workflow status mappings** (e.g., `CYCLE_START_STATUSES`).
*   **Key Technologies/Libraries:** Python 3.9+, `requests`, `pandas` (planned), `python-dotenv`, `pytest`, `requests-mock`.

## 4. Getting Started

### Prerequisites
*   Python 3.9+
*   `pip` and `virtualenv` (recommended)
*   Jira Instance Access
*   **Jira Password:** Your Jira account password.

### Installation
1.  Clone repository.
2.  Create/activate virtual environment: `python -m venv venv`, `source venv/bin/activate`.
3.  Install dependencies: `pip install -r requirements.txt`.
4.  **Set up Environment Variables:**
    *   Create a `.env` file in the project root (copy from `.env.example`).
    *   Fill in `JIRA_URL`, `JIRA_EMAIL`, `JIRA_PASSWORD`. This file is ignored by Git.
5.  **Configure Workflow Statuses (Crucial for Metric Calculation):**
    *   Edit `config.py`.
    *   Update the `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, and `THROUGHPUT_DONE_STATUSES` lists with the exact Jira status names used in your workflow(s). See comments in `config.py` for examples and guidance. This step is essential for accurate metric calculations later.

### Running the Application
```bash
# To test Jira connection and issue/changelog fetching (edit JQL in the script for your instance):
# Ensure .env and config.py are set up, then run from the project root:
# python src/jira_connector.py

# Full application execution via main.py (will be developed further).
```
### Running Tests
```bash
# Ensure virtual environment is active and dependencies installed
python -m pytest
```

## 5. Development Workflow & Contribution Guidelines

Strict Incremental Development Workflow is followed. Refer to `GEMINI_MASTER_GUIDANCE.md` Section II.1.

Key Guidelines: Adhere to `GEMINI_MASTER_GUIDANCE.md`, PEP 8, Clarity, Modularity, Configuration-driven, Testing.

## 6. Project Structure (High-Level)
```
jira-insights/
├── .env                # Local environment variables (SECRET, DO NOT COMMIT)
├── .env.example        # Example environment variables
├── .gitignore          # Specifies intentionally untracked files
├── config.py           # Project configurations, constants, STATUS MAPPINGS
├── main.py             # Main application script
├── src/                # Core source code
│   ├── __init__.py
│   ├── jira_connector.py # Jira API interaction & changelog parsing
│   ├── data_processor.py # Metric calculations (planned)
│   └── reporting.py      # Output generation (planned)
├── tests/              # Unit tests
│   ├── __init__.py
│   ├── conftest.py       # Pytest configuration (path setup)
│   ├── test_data_processor.py
│   └── test_jira_connector.py
├── requirements.txt    # Python package dependencies
├── PROJECT_PURPOSE.md
├── README.md           # This file
├── PROJECT_METRICS_SPECIFICATIONS.md
├── IMPROVEMENTS.md     # Task backlog
└── GEMINI_MASTER_GUIDANCE.md
```

## 7. Key Technologies

*   **Language:** Python 3.9+
*   **Core Libraries:** `python-dotenv`, `requests`, `pandas` (planned)
*   **Testing:** `pytest`, `requests-mock`

## 8. Future Roadmap (High-Level)

*   Implementation of metric calculations (Lead Time, Throughput, Cycle Time) in `data_processor.py` using configured statuses.
*   Command-line interface for flexible execution.
*   See `IMPROVEMENTS.md` for details.

## 9. Disclaimer

Accuracy depends on Jira data and tool configuration (especially status mappings in `config.py`).
**Security Note:** Uses Basic Authentication. Protect your `.env` file.