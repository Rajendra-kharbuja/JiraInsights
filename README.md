# Jira Insights

<!-- One-liner description of the project -->
A Python tool to fetch and analyze Jira data for Scrum Masters to gain insights into team performance, project health, and process bottlenecks across multiple teams.

## 1. Overview
<!-- Expand slightly on the project's purpose and what it does. Reference PROJECT_PURPOSE.md -->
**Jira Insights** is a Python application designed to **automate the collection and analysis of data from Jira projects and boards**. It addresses the challenge faced by Scrum Masters managing multiple teams by connecting to the Jira API using Basic Authentication, fetching relevant ticket information (including ID, key, type, status, created/resolved dates, and **issue changelog for status transition history**) via JQL with pagination. In future steps, it will calculate key agile metrics and provide structured output.

For a detailed understanding of the project's goals, scope, and philosophy, please see `PROJECT_PURPOSE.md`.

## 2. Features (Current / Planned for MVP)
<!-- List key features. Align with "In Scope" from PROJECT_PURPOSE.md -->
*   **Jira Connectivity:** Securely connect to Jira Cloud or Server using Jira Basic Authentication (Email/Password loaded from `.env`).
*   **Data Fetching:**
    *   Retrieve essential issue data (ID, key, type, status, created/resolved dates by default; other fields specifiable) from Jira via JQL queries, with robust pagination handling.
    *   Fetch issue **changelog** (via `expand=changelog` API parameter) and parse it to extract a chronologically sorted list of status transitions for each issue (stored under `status_transitions` key).
*   **Configurable Scope (Planned):** Specify target Jira projects and/or boards via configuration (`config.py`) or command-line arguments.
*   **Cycle Time Calculation (Planned):** Determine the time taken for issues to move between user-configurable workflow stages using the parsed `status_transitions`.
*   **Lead Time Calculation (Planned):** Determine the total time from issue creation to resolution using fetched date fields.
*   **Throughput Calculation (Planned):** Measure the number of items completed per time period.
*   **Basic Data Output (Planned):** Provide calculated metrics in accessible formats.
*   *(Planned) Basic Work-In-Progress (WIP) calculation.*
*   *(Planned) Generation of data points for Cumulative Flow Diagrams (CFD).*

## 3. Core Building Blocks & Architecture (High-Level)
<!-- Describe the main components and how they fit together. This will evolve. -->
*   **Input:** Jira REST API, Configuration files (`config.py`, `.env`), Command-line arguments (planned).
*   **Processing:**
    *   `src/jira_connector.py`: Handles authentication (Basic Auth), API calls (fetching issues via JQL including pagination and `changelog` expansion), connection testing, and parsing of status transitions from the changelog.
    *   `src/data_processor.py` (Planned): Cleans, transforms raw Jira data. Calculates metrics using fetched fields and `status_transitions`.
    *   `src/reporting.py` (Planned): Formats and outputs calculated metrics.
    *   `main.py`: Main script to orchestrate the workflow.
*   **Output:** Console logs (current), List of Dictionaries (from fetch function, now including `status_transitions`), CSV or JSON files (planned).
*   **Configuration:** Managed via `config.py` (non-sensitive) and `.env` (sensitive credentials).
*   **Key Technologies/Libraries:** Python 3.9+, `requests`, `pandas` (planned), `python-dotenv`, `pytest`, `requests-mock`.

## 4. Getting Started

### Prerequisites
*   Python 3.9+
*   `pip` and `virtualenv` (recommended)
*   Jira Instance Access (Cloud or Server)
*   **Jira Password:** Your Jira account password. Stored in `.env` (ignored by Git).

### Installation
1.  Clone repository.
2.  Create and activate virtual environment: `python -m venv venv`, `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
3.  Install dependencies: `pip install -r requirements.txt`.
4.  Set up `.env` file (copy from `.env.example`):
    ```dotenv
    JIRA_URL=https://your-domain.atlassian.net
    JIRA_EMAIL=your-email@example.com
    JIRA_PASSWORD=your_actual_password_here
    ```

### Running the Application
```bash
# To test Jira connection and issue/changelog fetching (edit JQL in the script for your instance):
# Ensure .env is set up, then run from the project root:
# python src/jira_connector.py

# Full application execution via main.py (will be developed further).
```
### Running Tests
```bash
# Ensure virtual environment is active and dependencies installed
python -m pytest
```

## 5. Development Workflow & Contribution Guidelines

Strict Incremental Development Workflow is followed. Refer to `GEMINI_MASTER_GUIDANCE.md` Section II.1. Key steps: Identify Task -> Analyze -> Plan (Seek Approval) -> Implement -> Test -> Document Task Status -> Document Code Changes -> Commit.

Key Guidelines: Adhere to `GEMINI_MASTER_GUIDANCE.md`, PEP 8, Clarity, Modularity, Configuration-driven, Testing.

## 6. Project Structure (High-Level)
```
jira-insights/
├── .env                # Local environment variables (SECRET, DO NOT COMMIT)
├── .env.example        # Example environment variables
├── .gitignore          # Specifies intentionally untracked files
├── config.py           # Project configurations, constants
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

*   Calculation of core agile metrics (Lead Time, Throughput, Cycle Time using fetched changelogs).
*   Command-line interface for flexible execution.
*   See `IMPROVEMENTS.md` for details.

## 9. Disclaimer

Accuracy depends on Jira data and tool configuration. Use for insights, not absolute measures.
**Security Note:** Uses Basic Authentication (password in `.env`). Protect `.env` locally. API Tokens are generally more secure.