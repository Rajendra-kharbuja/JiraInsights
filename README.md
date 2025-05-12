# Jira Insights

<!-- One-liner description of the project -->
A Python tool to fetch and analyze Jira data for Scrum Masters to gain insights into team performance, project health, and process bottlenecks across multiple teams.

## 1. Overview
<!-- Expand slightly on the project's purpose and what it does. Reference PROJECT_PURPOSE.md -->
**Jira Insights** is a Python application designed to **automate the collection and analysis of data from Jira projects and boards**. It addresses the challenge faced by Scrum Masters managing multiple teams (potentially mixed Scrum/Kanban) of manually gathering data to understand progress, identify bottlenecks, and track improvements. It achieves this by connecting to the Jira API, fetching relevant ticket and sprint information using JQL, calculating key agile metrics (like Cycle Time, Lead Time, Throughput), and providing structured output for analysis.

For a detailed understanding of the project's goals, scope, and philosophy, please see `PROJECT_PURPOSE.md`.

## 2. Features (Current / Planned for MVP)
<!-- List key features. Align with "In Scope" from PROJECT_PURPOSE.md -->
*   **Jira Connectivity:** Securely connect to Jira Cloud or Server using API tokens loaded from `.env`.
*   **Configurable Scope:** Specify target Jira projects and/or board IDs via configuration (`config.py`) or command-line arguments.
*   **Data Fetching:** Retrieve essential issue data including status transitions (changelog) and sprint details using JQL. Handles API pagination.
*   **Cycle Time Calculation:** Determine the time taken for issues to move between user-configurable workflow stages (defined in `config.py`).
*   **Lead Time Calculation:** Determine the total time from issue creation to resolution.
*   **Throughput Calculation:** Measure the number of items completed per time period (e.g., weekly, monthly).
*   **Basic Data Output:** Provide calculated metrics in accessible formats (e.g., console output, CSV/JSON files).
*   *(Planned) Basic Work-In-Progress (WIP) calculation.*
*   *(Planned) Generation of data points for Cumulative Flow Diagrams (CFD).*

## 3. Core Building Blocks & Architecture (High-Level)
<!-- Describe the main components and how they fit together. This will evolve. -->
*   **Input:** Jira REST API, Configuration files (`config.py`, `.env`), Command-line arguments.
*   **Processing:**
    *   `src/jira_connector.py`: Handles authentication, API calls (fetching issues via JQL, boards, sprints), and pagination logic.
    *   `src/data_processor.py`: Cleans, transforms raw Jira data (likely using `pandas`). Calculates metrics (Cycle Time, Lead Time, Throughput, WIP) based on status transitions and dates, guided by `config.py` settings.
    *   `src/reporting.py`: Formats and outputs the calculated metrics and insights (e.g., to console, files).
    *   `main.py`: Main script to orchestrate the workflow (configure -> connect -> fetch -> process -> report). Parses arguments/config.
*   **Output:** Console logs, CSV or JSON files containing calculated metrics or data points for charts (like CFD).
*   **Configuration:** Core settings (API endpoints, metric definitions like cycle time start/end statuses, JQL fragments) managed via `config.py`. Sensitive credentials (API token, email, Jira URL) and environment-specific settings managed via `.env`.
*   **Key Technologies/Libraries:** Python 3.9+, `requests`, `pandas`, `python-dotenv`, `pytest`. Potentially `typer` or `argparse` for CLI.

## 4. Getting Started

### Prerequisites
*   Python 3.9+
*   `pip` and `virtualenv` (recommended)
*   Jira Instance Access (Cloud or Server)
*   Jira API Token:
    *   Generate an API Token from your Atlassian Account settings: [https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
    *   You will need your Jira URL (e.g., `https://your-domain.atlassian.net`), the email associated with the token, and the token itself. Store these in a `.env` file.

### Installation
1.  Clone the repository:
    ```bash
    # Replace with actual URL when available
    # git clone [REPOSITORY_URL]
    # cd jira-insights
    ```
2.  Create and activate a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install dependencies:
    ```bash
    # Ensure requirements.txt exists first
    pip install -r requirements.txt
    ```
4.  Set up environment variables:
    *   Create a `.env` file in the project root (you can copy `.env.example` if provided).
    *   Add necessary configurations:
        ```dotenv
        JIRA_URL=https://your-domain.atlassian.net
        JIRA_EMAIL=your-email@example.com
        JIRA_API_TOKEN=your_api_token_here
        ```
    *   Refer to `config.py` for other non-sensitive configuration settings.

### Running the Application
<!-- How to run the main part of the project -->
```bash
# Example command (will be refined as CLI develops)
# python main.py --projects PROJ1,PROJ2 --output metrics.csv
```

### Running Tests
```bash
pytest
```

## 5. Development Workflow & Contribution Guidelines

This project uses a strict Incremental Development Workflow where code and documentation changes are tightly synchronized. All contributions, including those from AI assistants, must follow this process and the guidelines below. Refer to [`GEMINI_MASTER_GUIDANCE.md`](GEMINI_MASTER_GUIDANCE.md) Section II.1 for the detailed workflow diagram and steps.

Identify Task: Select from [`IMPROVEMENTS.md`](IMPROVEMENTS.md).

Analyze: Understand task in full project context (code + all docs).

Plan: Propose code, test, and all documentation update plans. Seek approval before coding.

Implement: Write clean, commented, PEP 8 compliant Python code.

Test: Add/run unit tests (pytest).

Document Task Status: Update [`IMPROVEMENTS.md`](IMPROVEMENTS.md).

Document Code Changes: Update this [`README.md`](README.md), [`PROJECT_METRICS_SPECIFICATIONS.md`](PROJECT_METRICS_SPECIFICATIONS.md), [`config.py`](config.py) comments, add inline comments, etc. This is mandatory.

Commit (Simulated): Group related code, test, and all documentation changes into a single unit.

Key Guidelines:

Adhere to [`GEMINI_MASTER_GUIDANCE.md`](GEMINI_MASTER_GUIDANCE.md): AI assistants must follow the detailed guidance provided there (Version 1.1+).

PEP 8: All Python code must follow PEP 8 standards.

Clarity & Simplicity: Prioritize readable code and clear documentation.

Modularity: Maintain logical separation of concerns (connection, processing, reporting).

Configuration: Use [`config.py`](config.py) for non-sensitive settings/rules and `.env` for secrets/environment specifics. Document configurations clearly.

Error Handling: Implement robust error handling, especially around API calls and data parsing.

Testing: Unit tests are crucial for data processing logic. Mock API calls for connector tests.

## 6. Project Structure (High-Level)
```
jira-insights/
├── .env                # Local environment variables (DO NOT COMMIT)
├── .env.example        # Example environment variables
├── config.py           # Project configurations, constants, metric definitions
├── main.py             # Main application script/entry point
├── src/                # Core source code directory
│   ├── __init__.py
│   ├── jira_connector.py # Module for Jira API interaction
│   ├── data_processor.py # Module for data cleaning and metric calculation
│   └── reporting.py      # Module for output generation
├── data/               # (Optional) For storing output files (e.g., CSVs) - add to .gitignore
├── tests/              # Unit and integration tests
│   ├── __init__.py
│   ├── test_data_processor.py
│   └── test_jira_connector.py # (Will likely require mocking)
├── PROJECT_PURPOSE.md  # Goals, scope, users
├── README.md           # This file (Technical overview, setup, workflow)
├── PROJECT_METRICS_SPECIFICATIONS.md # Details on data points and metrics
├── IMPROVEMENTS.md     # Task backlog (Bugs, Features, Enhancements)
└── GEMINI_MASTER_GUIDANCE.md # Guidance for AI assistant collaboration
```

## 7. Key Technologies

Language: Python 3.9+

Core Libraries:

*   `requests` (for Jira API communication)
*   `pandas` (for data manipulation and analysis)
*   `python-dotenv` (for environment variable management)

Testing: `pytest`

CLI (Potential): `argparse` or `typer`

## 8. Future Roadmap (High-Level)
<!-- Link to or summarize items from IMPROVEMENTS.md tagged as major features -->

*   Generation of data suitable for visualization (e.g., CFD, Control Charts).
*   Addition of more sophisticated metrics (e.g., WIP analysis, sprint-specific reporting).
*   Potential web-based UI for easier configuration and viewing results (e.g., using Streamlit or Flask).
*   Analysis of issue links between different boards/projects.

See [`IMPROVEMENTS.md`](IMPROVEMENTS.md) for a detailed, prioritized list.

## 9. Disclaimer

This tool provides insights based on data extracted from Jira. The accuracy of the insights depends heavily on the accuracy and consistency of the data within Jira (e.g., timely status updates) and the correct configuration of the tool (e.g., status mappings in [`config.py`](config.py)). Use the results to inform discussions, identify areas for investigation, and track trends, not as absolute, infallible measures of performance. Ensure compliance with your organization's data access policies when configuring and using this tool.

---