# config.py
# Holds non-sensitive configuration settings, constants, and mappings for Jira Insights.

# --- Jira Status Mappings (REQUIRED - User must configure these) ---
# Define the exact Jira status names that correspond to the start and end of your cycle time measurement.
# Example: CYCLE_START_STATUSES = ["In Progress"]
# Example: CYCLE_END_STATUSES = ["Resolved", "Closed", "Done"]
CYCLE_START_STATUSES = []
CYCLE_END_STATUSES = []

# Define statuses considered "Done" for Throughput calculation (if different from Cycle End)
# Example: THROUGHPUT_DONE_STATUSES = ["Resolved", "Closed", "Done"]
# If empty, will likely default to using ResolutionDate or CYCLE_END_STATUSES.
THROUGHPUT_DONE_STATUSES = []

# (Future) Mapping for CFD columns
# Example: CFD_COLUMN_MAPPING = {
#    "ToDo": ["Backlog", "To Do", "Selected for Development"],
#    "Dev": ["In Progress", "Code Review"],
#    "Test": ["In QA", "UAT"],
#    "Done": ["Resolved", "Closed", "Done"]
# }
CFD_COLUMN_MAPPING = {}

# --- API Settings ---
# Base URL is usually handled via .env, but specific paths can go here if needed.
JIRA_API_SEARCH_PATH = "/rest/api/3/search"
JIRA_API_MYSELF_PATH = "/rest/api/3/myself" # Used by jira_connector for testing connection

# --- Default Settings ---
DEFAULT_OUTPUT_FILENAME = "jira_insights_output.csv"

print("INFO [config.py]: config.py loaded/parsed.") # Diagnostic print