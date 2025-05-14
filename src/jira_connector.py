# src/jira_connector.py
# Handles connection and data fetching from the Jira API using Basic Authentication.

import os
import sys
import requests
import logging
from dotenv import load_dotenv, find_dotenv
from typing import Optional, Tuple, List, Dict, Any # Added List, Dict, Any

# config.py is at the project root and pytest runs from root, adding it to sys.path
print(f"DEBUG [jira_connector.py]: sys.path at import time = {sys.path}")
try:
    import config
    print("DEBUG [jira_connector.py]: Successfully imported 'config'.")
except ModuleNotFoundError as e:
    print(f"ERROR [jira_connector.py]: Failed to import 'config'. Error: {e}")
    raise

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

def load_credentials() -> Optional[Tuple[str, str, str]]:
    """
    Loads Jira URL, email, and password from the .env file.

    Returns:
        A tuple containing (jira_url, jira_email, jira_password) if all are found,
        otherwise None.
    """
    env_path = find_dotenv(raise_error_if_not_found=False)
    if env_path:
        print(f"DEBUG [jira_connector.py]: Loading .env from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print("DEBUG [jira_connector.py]: .env file not found by find_dotenv(). Relying on os.getenv directly.")

    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_password = os.getenv("JIRA_PASSWORD")

    if not jira_url:
        logging.error("JIRA_URL not found or is empty in environment variables / .env file.")
    if not jira_email:
        logging.error("JIRA_EMAIL not found or is empty in environment variables / .env file.")
    if not jira_password:
        logging.error("JIRA_PASSWORD not found or is empty in environment variables / .env file.")

    if not all([jira_url, jira_email, jira_password]):
        logging.error("Missing one or more required Jira credentials.")
        return None

    if not jira_url.startswith(('http://', 'https://')):
         logging.error(f"Invalid JIRA_URL format: '{jira_url}'. Must start with http:// or https://")
         return None

    return jira_url.rstrip('/'), jira_email, jira_password


def test_jira_connection() -> bool:
    """
    Tests the connection and authentication to the Jira API using Basic Auth.

    Returns:
        True if the connection and authentication are successful, False otherwise.
    """
    credentials = load_credentials()
    if not credentials:
        return False

    jira_url, jira_email, jira_password = credentials
    test_endpoint = config.JIRA_API_MYSELF_PATH
    test_url = f"{jira_url}{test_endpoint}"

    logging.info(f"Attempting to connect to Jira at {jira_url} using Basic Auth as {jira_email}...")

    try:
        response = requests.get(
            test_url,
            auth=(jira_email, jira_password),
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=15
        )
        response.raise_for_status()

        try:
            user_data = response.json()
            display_name = user_data.get('displayName', 'N/A')
            logging.info(f"Jira connection and authentication successful. Authenticated as: {display_name} ({jira_email})")
        except requests.exceptions.JSONDecodeError:
             logging.warning("Authentication successful, but failed to decode JSON response from /myself endpoint.")
        return True

    except requests.exceptions.ConnectionError as e:
        logging.error(f"Connection Error: Failed to connect to Jira URL '{jira_url}'. Check URL and network connectivity. Details: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        if status_code == 401:
            logging.error(f"Authentication Failed (401 Unauthorized): Invalid email or password for user '{jira_email}'.")
        elif status_code == 403:
            logging.error(f"Authorization Failed (403 Forbidden): User '{jira_email}' may lack permissions, CAPTCHA required, or Basic Auth restricted.")
        elif status_code == 404:
            logging.error(f"API Endpoint Not Found (404): Check JIRA_URL ('{jira_url}') and API path ('{test_endpoint}').")
        else:
            logging.error(f"HTTP Error: Received status code {status_code} from Jira. Details: {e.response.text}") # Added .text for more detail
        return False
    except requests.exceptions.Timeout:
        logging.error(f"Request Timeout: The request to Jira timed out after 15 seconds.")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"An unexpected error occurred during the Jira request: {e}")
        return False
    except Exception as e:
        logging.exception(f"An unexpected non-request error occurred: {e}")
        return False

# --- NEW FUNCTION ---
def fetch_issues_by_jql(
    jql_query: str,
    fields: Optional[List[str]] = None,
    max_issues_to_fetch: Optional[int] = None
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches issues from Jira based on a JQL query, handling pagination.

    Args:
        jql_query: The JQL query string.
        fields: A list of Jira field names to retrieve.
                If None, defaults to a predefined set for core metrics:
                ["id", "key", "issuetype", "status", "created", "resolutiondate"].
        max_issues_to_fetch: An optional maximum number of issues to fetch.
                             If None, fetches all matching issues.

    Returns:
        A list of dictionaries, where each dictionary represents a Jira issue,
        or None if an error occurs during connection or fetching.
    """
    credentials = load_credentials()
    if not credentials:
        return None

    jira_url, jira_email, jira_password = credentials
    search_url = f"{jira_url}{config.JIRA_API_SEARCH_PATH}"

    if fields is None:
        # Default fields as per PROJECT_METRICS_SPECIFICATIONS.md (Initial Scope)
        # These are the string representations of the field IDs/names Jira expects.
        fields = ["id", "key", "issuetype", "status", "created", "resolutiondate"]
        # Note: Actual field data will be nested under 'fields' in the response, e.g., issue['fields']['summary']
        # For standard fields like 'id' and 'key', they are top-level.

    all_issues: List[Dict[str, Any]] = []
    start_at = 0
    # max_results_per_page can be up to 100 for Jira Cloud, sometimes less for Server.
    # Using a slightly conservative default to be safe, or configurable.
    max_results_per_page = 50 # Configurable: could be moved to config.py

    logging.info(f"Initiating JQL search: \"{jql_query}\"")
    logging.debug(f"Fields to retrieve: {', '.join(fields)}")

    page_num = 1
    while True:
        params = {
            "jql": jql_query,
            "startAt": start_at,
            "maxResults": max_results_per_page,
            "fields": ",".join(fields)  # Jira API expects comma-separated string
        }
        logging.info(f"Requesting page {page_num}: startAt={start_at}, maxResults={max_results_per_page}")

        try:
            response = requests.get(
                search_url,
                auth=(jira_email, jira_password),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                params=params,
                timeout=30  # Increased timeout for search queries
            )
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            current_page_issues = data.get("issues", [])
            all_issues.extend(current_page_issues)

            total_issues_on_server = data.get("total", 0) # Total matching issues on server

            logging.debug(f"Page {page_num}: Received {len(current_page_issues)} issues. "
                         f"Cumulative fetched: {len(all_issues)}. Server reports total: {total_issues_on_server}.")

            # Check if max_issues_to_fetch limit is reached
            if max_issues_to_fetch is not None and len(all_issues) >= max_issues_to_fetch:
                logging.info(f"Reached configured max_issues_to_fetch ({max_issues_to_fetch}). "
                             f"Stopping pagination. Returning {max_issues_to_fetch} issues.")
                return all_issues[:max_issues_to_fetch] # Slice to return exactly max_issues_to_fetch

            # Determine if pagination should continue
            if not current_page_issues: # No issues on this page
                logging.info("No more issues returned on current page. Pagination complete.")
                break
            
            start_at += len(current_page_issues) # Correctly increment startAt
            page_num += 1

            if start_at >= total_issues_on_server: # Fetched all available issues
                logging.info(f"Fetched {start_at} issues, matching server total {total_issues_on_server}. Pagination complete.")
                break
            
            # An alternative check: if len(current_page_issues) < max_results_per_page, it's likely the last page.
            # However, relying on startAt >= total is more robust.

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error during JQL search (page {page_num}, startAt {start_at}): "
                          f"{e.response.status_code} - {e.response.text}")
            return None # Or re-raise a custom exception
        except requests.exceptions.RequestException as e: # Catches ConnectionError, Timeout, etc.
            logging.error(f"Request Exception during JQL search (page {page_num}, startAt {start_at}): {e}")
            return None
        except Exception as e: # Catch-all for other unexpected errors
            logging.exception(f"An unexpected error occurred during JQL search (page {page_num}, startAt {start_at}): {e}")
            return None

    logging.info(f"JQL search completed. Successfully fetched a total of {len(all_issues)} issues.")
    return all_issues


if __name__ == "__main__":
    print("Running Jira connection test directly from jira_connector.py...")
    connection_ok = test_jira_connection()
    if connection_ok:
        print("\nConnection Test Result (direct run): PASSED")

        # --- Test issue fetching ---
        print("\n--- Testing issue fetching ---")
        # IMPORTANT: User must adapt this JQL to their Jira instance for direct testing.
        # Example: Find 2 issues in project 'YOUR_PROJECT_KEY', most recently created first
        sample_jql = "project = MYPROJ ORDER BY created DESC" # !!! REPLACE MYPROJ with a valid project key !!!
        # sample_jql = "assignee = currentUser() AND resolution = Unresolved ORDER BY priority DESC, updated DESC"
        sample_fields = ["summary", "status", "issuetype", "created", "resolutiondate", "project"]
        
        print(f"Attempting to fetch issues with JQL: \"{sample_jql}\"")
        # Fetch a small number for direct testing
        issues = fetch_issues_by_jql(jql_query=sample_jql, fields=sample_fields, max_issues_to_fetch=5)

        if issues is not None:
            print(f"\nFetched {len(issues)} issues successfully:")
            for i, issue in enumerate(issues):
                issue_fields = issue.get('fields', {})
                status_info = issue_fields.get('status', {})
                project_info = issue_fields.get('project', {})
                print(f"  Issue {i+1}: Key={issue.get('key')}, "
                      f"Project={project_info.get('key', 'N/A')}, "
                      f"Summary=\"{issue_fields.get('summary', 'N/A')}\", "
                      f"Status={status_info.get('name', 'N/A')}")
                if i == 4 and len(issues) == 5 : # max_issues_to_fetch was 5
                     print("  (Reached max_issues_to_fetch for this direct test run)")

            if not issues:
                print("  No issues found matching the JQL query (or max_issues_to_fetch was 0).")
        else:
            print("  Failed to fetch issues. Check logs above for errors.")
    else:
        print("\nConnection Test Result (direct run): FAILED - Check logs above for details.")
        print("  Skipping issue fetching test due to connection failure.")