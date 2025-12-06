# Jira Insights

<!-- One-liner description of the project -->
A Python tool to fetch and analyze Jira data for Scrum Masters to gain insights into team performance, project health, and process bottlenecks across multiple teams.

## 1. Overview
<!-- Expand slightly on the project's purpose and what it does. Reference PROJECT_PURPOSE.md -->
**Jira Insights** is a Python application designed to **automate the collection and analysis of data from Jira projects and boards**. It connects to Jira using Basic Authentication, fetches ticket information (including status transition history), and calculates key agile metrics like **Cycle Time** and **Lead Time**. User-specific workflow configurations in `config.py` are essential for accurate metric calculation. Future enhancements will include Throughput, WIP analysis, and more.

For a detailed understanding of the project's goals, scope, and philosophy, please see `PROJECT_PURPOSE.md`.

## 2. Features (Current / Planned for MVP)
<!-- List key features. Align with "In Scope" from PROJECT_PURPOSE.md -->
*   **Jira Connectivity:** Connects to Jira (Cloud/Server) using Basic Authentication (Email/Password from `.env`).
*   **Data Fetching:**
    *   Retrieves issue data (default fields in `config.py`; others specifiable) via JQL, with pagination.
    *   Fetches and parses issue **changelog** for a sorted list of status transitions.
*   **Configurable Workflow Statuses:** User-defined mappings in `config.py` for `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, etc.
*   **Cycle Time Calculation:** Calculates cycle time based on status transitions and configured workflow statuses. Output unit configurable (default: days).
*   **Lead Time Calculation:** Calculates lead time (creation to resolution) using fetched date fields. Output unit configurable (default: days).
*   **Configurable Scope (Planned).**
*   **Throughput Calculation (Planned).**
*   **Basic Data Output (Planned).**

## 3. Core Building Blocks & Architecture (High-Level)
<!-- Describe the main components and how they fit together. This will evolve. -->
*   **Input:** Jira REST API, `config.py`, `.env`.
*   **Processing:**
    *   `src/jira_connector.py`: Handles authentication, API calls, status transition parsing.
    *   `src/data_processor.py`: Contains logic for metric calculations (Cycle Time, Lead Time).
    *   `src/reporting.py` (Planned): Output formatting.
    *   `main.py`: Orchestrates the workflow (planned).
*   **Output:** Console logs, List of Dictionaries (issues with metrics), CSV/JSON (planned).
*   **Configuration:** `.env` for secrets; `config.py` for API paths, defaults, and **user-defined Jira workflow status mappings**.
*   **Key Technologies:** Python, `requests`, `python-dotenv`, `pytest`, `requests-mock`. `pandas` planned.

## 4. Getting Started

### Prerequisites
*   Python 3.9+
*   `pip`, `virtualenv`
*   Jira Access & Password

### Installation
1.  Clone repository.
2.  Set up virtual environment & activate.
3.  Install dependencies: `pip install -r requirements.txt`.
4.  **Set up `.env` file:** (Copy from `.env.example`)
    ```dotenv
    JIRA_URL=https://your-domain.atlassian.net
    JIRA_EMAIL=your-email@example.com
    JIRA_PASSWORD=your_actual_password_here
    ```
5.  **Configure Workflow Statuses (Crucial!):**
    *   Edit `config.py`.
    *   Update `CYCLE_START_STATUSES`, `CYCLE_END_STATUSES`, and `THROUGHPUT_DONE_STATUSES` lists.

### Running the Application
```bash
# To test Jira connection and basic data fetching/processing:
# 1. Ensure .env and config.py (status mappings) are set up.
# 2. Edit sample JQL in __main__ block of relevant .py file (e.g., src/jira_connector.py).
# 3. Run from project root: python src/jira_connector.py OR python src/data_processor.py (if it has test code)

# Full application execution via main.py (to be developed).
```
### Running Tests
```bash
python -m pytest
```

## 5. Development Workflow & Contribution Guidelines

Strict Incremental Development Workflow. See `GEMINI_MASTER_GUIDANCE.md` Section II.1.

Key Guidelines: Adhere to `GEMINI_MASTER_GUIDANCE.md`, PEP 8, Clarity, Modularity, Config-driven, Testing.

## 6. Project Structure (High-Level)
```
jira-insights/
├── .env, .env.example, .gitignore
├── config.py           # Configs, STATUS MAPPINGS
├── main.py
├── src/
│   ├── __init__.py
│   ├── jira_connector.py # API interaction, changelog parsing
│   ├── data_processor.py # Cycle/Lead Time & other metric calculations
│   └── reporting.py      # (planned)
├── tests/
│   ├── __init__.py, conftest.py
│   ├── test_data_processor.py
│   └── test_jira_connector.py
├── requirements.txt
├── PROJECT_PURPOSE.md, README.md, PROJECT_METRICS_SPECIFICATIONS.md
├── IMPROVEMENTS.md, GEMINI_MASTER_GUIDANCE.md
```

## 7. Key Technologies

*   Python 3.9+, `python-dotenv`, `requests`
*   Testing: `pytest`, `requests-mock`
*   Data Processing (planned): `pandas`

## 8. Future Roadmap (High-Level)

*   Implementation of Throughput calculation.
*   Command-line interface.
*   See `IMPROVEMENTS.md`.

## 9. Disclaimer

Accuracy depends on Jira data and `config.py` status mappings.
**Security Note:** Uses Basic Auth. Protect `.env`. API Tokens preferred.