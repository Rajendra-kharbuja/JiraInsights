# config.py
# Holds non-sensitive configuration settings, constants, and mappings for Jira Insights.

print("INFO [config.py]: config.py loaded/parsed.") # Diagnostic print

# --- Jira Workflow Status Mappings (USER CONFIGURATION REQUIRED) ---
# These lists define which of YOUR Jira workflow statuses map to key points for metric calculations.
# You MUST update these lists with the exact names of your Jira statuses.
# Case-sensitivity might matter depending on how comparisons are made later.
# It's generally safer to match the case exactly as it appears in your Jira workflow.

# CYCLE TIME CONFIGURATION:
# Define statuses that signify the START of your active development cycle.
# This is the point from which you want to measure how long an item takes.
# Example: If work starts when an issue moves to "In Progress" or "Development".
# CYCLE_START_STATUSES = ["In Progress", "Development"]
CYCLE_START_STATUSES: list[str] = [
    # "Example: In Progress",
    # "Example: Development Started"
]

# Define statuses that signify the END of your active development cycle.
# This is the point at which you consider the measured cycle complete.
# Example: If cycle ends when an issue is "Ready for QA", "Resolved", or "Testing Complete".
# It could also be your final "Done" status if you want to measure the full active flow to completion.
# CYCLE_END_STATUSES = ["Resolved", "Ready for QA", "Closed"]
CYCLE_END_STATUSES: list[str] = [
    # "Example: Resolved",
    # "Example: Ready for Release"
]

# THROUGHPUT CONFIGURATION:
# Define statuses that are considered "completed" or "done" for the purpose of calculating throughput
# (i.e., number of items finished per unit of time).
# This might be the same as CYCLE_END_STATUSES, or it could be a more final set of statuses
# (e.g., if Cycle End is "Ready for Release" but Throughput measures "Released" or "Done").
# If this list is empty, the system might default to using `resolutiondate` for throughput,
# or it might use CYCLE_END_STATUSES if `resolutiondate` is unreliable. This behavior will be
# confirmed when throughput calculation (FEAT-007) is implemented.
# Example: THROUGHPUT_DONE_STATUSES = ["Closed", "Done", "Released"]
THROUGHPUT_DONE_STATUSES: list[str] = [
    # "Example: Done",
    # "Example: Released to Production"
]


# --- CFD (Cumulative Flow Diagram) Column Mapping (USER CONFIGURATION REQUIRED - For Future CFD Feature - ENH-005) ---
# This dictionary maps your Jira statuses to logical columns for a CFD.
# The keys are the column names you want on your CFD (e.g., "01 - ToDo", "02 - In Dev").
# The values are lists of Jira status names that belong to that column.
# The order of keys in the dictionary will likely determine the order of columns on the CFD.
# Ensure all statuses that an issue can pass through (from backlog to final done) are mapped.
# Example:
# CFD_COLUMN_MAPPING: dict[str, list[str]] = {
#    "01 - ToDo": ["Backlog", "To Do", "Selected for Development"],
#    "02 - Development": ["In Progress", "Code Review"],
#    "03 - Testing": ["In QA", "Ready for UAT", "UAT"],
#    "04 - Ready To Deploy": ["Ready for Release"],
#    "05 - Done": ["Resolved", "Closed", "Done", "Released"]
# }
CFD_COLUMN_MAPPING: dict[str, list[str]] = {
    # "Example CFD Column 1 (e.g., Backlog)": ["Open", "Refinement"],
    # "Example CFD Column 2 (e.g., In Progress)": ["Development", "In Review"],
    # "Example CFD Column 3 (e.g., Done)": ["Closed", "Deployed"],
}


# --- API Settings ---
# Base URL for Jira is handled via .env (JIRA_URL).
# These are specific API paths appended to the JIRA_URL.
JIRA_API_SEARCH_PATH = "/rest/api/3/search"      # For JQL searches
JIRA_API_MYSELF_PATH = "/rest/api/3/myself"      # Used by jira_connector for testing connection


# --- Default Application Settings ---
DEFAULT_OUTPUT_FILENAME = "jira_insights_output.csv" # Default filename for CSV exports (FEAT-008)

# Default max results per API page request when fetching issues from Jira.
# Jira's own default is usually 50. The absolute maximum is often 100.
# Keeping it at 50 is generally safe and reduces memory per request.
JIRA_MAX_RESULTS_PER_PAGE = 50

# Default fields to fetch if not specified by the caller of fetch_issues_by_jql.
# These are the string representations of field IDs/names Jira API expects.
# Note: 'id' and 'key' are top-level in the issue JSON.
# Others like 'issuetype', 'status', 'created', 'resolutiondate', 'summary', 'project'
# are typically found nested under the 'fields' object in the Jira issue JSON.
# 'changelog' is handled separately via the 'expand' parameter.
DEFAULT_JIRA_FIELDS_TO_FETCH = [
    "id",                   # Top-level
    "key",                  # Top-level
    "summary",              # fields.summary
    "issuetype",            # fields.issuetype (object with name, id, etc.)
    "status",               # fields.status (object with name, id, statusCategory, etc.)
    "created",              # fields.created (ISO 8601 timestamp)
    "resolutiondate",       # fields.resolutiondate (ISO 8601 timestamp, nullable)
    "project",              # fields.project (object with key, name, id, etc.)
    # Add other common fields you might want by default:
    # "assignee",           # fields.assignee (object, nullable)
    # "reporter",           # fields.reporter (object)
    # "priority",           # fields.priority (object, nullable)
    # "labels",             # fields.labels (list of strings)
    # "components",         # fields.components (list of objects)
    # "fixVersions",        # fields.fixVersions (list of objects)
    # "duedate",            # fields.duedate (YYYY-MM-DD string, nullable)
    # "updated"             # fields.updated (ISO 8601 timestamp)
]