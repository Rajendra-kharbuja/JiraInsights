# src/jira_connector.py
# Handles connection and data fetching from the Jira API using Basic Authentication.

import os
import sys
import requests
import logging
from dotenv import load_dotenv, find_dotenv
from typing import Optional, Tuple, List, Dict, Any

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
    """Loads Jira URL, email, and password from the .env file."""
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
    """Tests the connection and authentication to the Jira API using Basic Auth."""
    credentials = load_credentials()
    if not credentials:
        return False
    jira_url, jira_email, jira_password = credentials
    test_endpoint = config.JIRA_API_MYSELF_PATH
    test_url = f"{jira_url}{test_endpoint}"
    logging.info(f"Attempting to connect to Jira at {jira_url} using Basic Auth as {jira_email}...")
    try:
        response = requests.get(
            test_url, auth=(jira_email, jira_password),
            headers={"Accept": "application/json", "Content-Type": "application/json"}, timeout=15
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
        logging.error(f"Connection Error: Failed to connect to Jira URL '{jira_url}'. Check URL and network. Details: {e}")
        return False
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        error_text = e.response.text # Get more detailed error from Jira
        if status_code == 401:
            logging.error(f"Authentication Failed (401 Unauthorized): Invalid email or password for user '{jira_email}'. Response: {error_text}")
        elif status_code == 403:
            logging.error(f"Authorization Failed (403 Forbidden): User '{jira_email}' may lack permissions, CAPTCHA, or Basic Auth restricted. Response: {error_text}")
        elif status_code == 404:
            logging.error(f"API Endpoint Not Found (404): Check JIRA_URL ('{jira_url}') and API path ('{test_endpoint}'). Response: {error_text}")
        else:
            logging.error(f"HTTP Error: Received status code {status_code} from Jira. Response: {error_text}")
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

# --- NEW HELPER FUNCTION ---
def _parse_status_transitions(changelog_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parses the 'changelog' object from a Jira issue to extract status transitions.

    Args:
        changelog_data: The 'changelog' dictionary from the Jira issue JSON.
                        Expected structure: {"startAt": ..., "maxResults": ..., "total": ..., "histories": [...]}

    Returns:
        A list of dictionaries, where each dictionary represents a status transition
        and has keys: "timestamp" (str), "from_status" (Optional[str]), "to_status" (str).
        Returns an empty list if no status transitions are found or changelog is malformed.
    """
    status_transitions: List[Dict[str, Any]] = []
    if not changelog_data or "histories" not in changelog_data:
        logging.debug("No changelog histories found in the provided data.")
        return status_transitions

    for history_item in changelog_data.get("histories", []):
        timestamp = history_item.get("created")
        if not timestamp:
            # Log a warning as this is unusual for a valid history item
            logging.warning(f"Changelog history item missing 'created' timestamp. History: {history_item}")
            continue

        for item in history_item.get("items", []):
            # Check for status field. Jira commonly uses 'status' for fieldId.
            # 'field' attribute might contain a display name like "Status".
            field_id = item.get("fieldId", "").lower()
            # field_name = item.get("field", "").lower() # Could also check field_name if fieldId is not "status"

            if field_id == "status": # Primary check
                from_status_name = item.get("fromString")  # Name of the previous status
                to_status_name = item.get("toString")      # Name of the new status

                # Ensure there's a 'to_status_name' to consider it a valid transition for our purposes
                if to_status_name is not None:
                    status_transitions.append({
                        "timestamp": timestamp,
                        "from_status": from_status_name, # Can be None for issue creation status
                        "to_status": to_status_name
                    })
                else:
                    logging.debug(f"Status change item in changelog missing 'toString' (new status name). Item: {item}")
    
    # Sort transitions by timestamp to ensure chronological order.
    # This is crucial for accurate cycle time calculations.
    if status_transitions:
        try:
            status_transitions.sort(key=lambda x: x["timestamp"])
        except TypeError as e:
            # This could happen if timestamps are malformed (e.g., None mixed with strings)
            # Though 'created' field in history should always be a valid timestamp string.
            logging.error(f"Error sorting status transitions due to invalid timestamp data: {e}. "
                          f"Transitions for this issue might be unsorted or incomplete.")
            # Depending on requirements, one might choose to filter out items with bad timestamps
            # or handle this more gracefully. For now, just log.

    return status_transitions

# --- MODIFIED FUNCTION ---
def fetch_issues_by_jql(
    jql_query: str,
    fields: Optional[List[str]] = None,
    max_issues_to_fetch: Optional[int] = None,
    include_changelog: bool = True # New parameter to control changelog fetching
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches issues from Jira based on a JQL query, handling pagination and optionally changelogs.

    Args:
        jql_query: The JQL query string.
        fields: A list of Jira field names to retrieve (e.g., "summary", "assignee").
                If None, defaults to a predefined set for core metrics:
                ["id", "key", "issuetype", "status", "created", "resolutiondate"].
                Note: 'id' and 'key' are usually top-level, others under 'fields' object in response.
        max_issues_to_fetch: An optional maximum number of issues to fetch.
                             If None, fetches all matching issues.
        include_changelog: If True, requests and parses the issue changelog for status transitions.

    Returns:
        A list of dictionaries, where each dictionary represents a Jira issue
        (with an added 'status_transitions' key if include_changelog is True),
        or None if an error occurs during connection or fetching.
    """
    credentials = load_credentials()
    if not credentials:
        return None

    jira_url, jira_email, jira_password = credentials
    search_url = f"{jira_url}{config.JIRA_API_SEARCH_PATH}"

    if fields is None:
        fields = ["id", "key", "issuetype", "status", "created", "resolutiondate"]

    all_fetched_issues_raw: List[Dict[str, Any]] = [] # Stores raw issues from API
    start_at = 0
    max_results_per_page = 50 # Or from config.py: config.JIRA_MAX_RESULTS_PER_PAGE

    logging.info(f"Initiating JQL search: \"{jql_query}\"")
    logging.debug(f"Fields to retrieve: {', '.join(fields)}. Include changelog: {include_changelog}")

    page_num = 1
    while True:
        request_params: Dict[str, Any] = { # Use Any for params dict value type
            "jql": jql_query,
            "startAt": start_at,
            "maxResults": max_results_per_page,
            "fields": ",".join(fields)
        }
        if include_changelog:
            request_params["expand"] = "changelog" # Add expand parameter for changelog

        logging.info(f"Requesting page {page_num}: startAt={start_at}, maxResults={max_results_per_page}, expand={request_params.get('expand', 'None')}")

        try:
            response = requests.get(
                search_url,
                auth=(jira_email, jira_password),
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                params=request_params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            current_page_issues = data.get("issues", [])
            all_fetched_issues_raw.extend(current_page_issues)

            total_issues_on_server = data.get("total", 0)

            logging.debug(f"Page {page_num}: Received {len(current_page_issues)} issues. "
                         f"Cumulative fetched raw: {len(all_fetched_issues_raw)}. Server reports total: {total_issues_on_server}.")

            if max_issues_to_fetch is not None and len(all_fetched_issues_raw) >= max_issues_to_fetch:
                logging.info(f"Reached/exceeded configured max_issues_to_fetch ({max_issues_to_fetch}). "
                             f"Stopping pagination. Raw issues fetched: {len(all_fetched_issues_raw)}.")
                # We will slice after parsing changelogs if needed, to ensure changelogs of all fetched raw issues are processed
                break # Exit pagination loop, will process and then slice

            if not current_page_issues:
                logging.info("No more issues returned on current page. Pagination complete.")
                break
            
            start_at += len(current_page_issues)
            page_num += 1

            if start_at >= total_issues_on_server:
                logging.info(f"Fetched {start_at} issues, matching/exceeding server total {total_issues_on_server}. Pagination complete.")
                break

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error during JQL search (page {page_num}, startAt {start_at}): "
                          f"{e.response.status_code} - {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Request Exception during JQL search (page {page_num}, startAt {start_at}): {e}")
            return None
        except Exception as e:
            logging.exception(f"An unexpected error occurred during JQL search (page {page_num}, startAt {start_at}): {e}")
            return None

    # Process changelogs if requested
    processed_issues: List[Dict[str, Any]] = []
    for issue_data in all_fetched_issues_raw:
        if include_changelog:
            parsed_transitions = []
            if "changelog" in issue_data and issue_data["changelog"] is not None:
                parsed_transitions = _parse_status_transitions(issue_data["changelog"])
            issue_data["status_transitions"] = parsed_transitions
        else:
            issue_data["status_transitions"] = [] # Ensure key exists but is empty
        processed_issues.append(issue_data)
    
    # Apply max_issues_to_fetch limit if it was set, after processing
    if max_issues_to_fetch is not None:
        processed_issues = processed_issues[:max_issues_to_fetch]
        logging.info(f"Returning final {len(processed_issues)} issues after applying max_issues_to_fetch limit.")


    logging.info(f"JQL search and processing completed. Returning {len(processed_issues)} issues.")
    return processed_issues


if __name__ == "__main__":
    print("Running Jira connection test directly from jira_connector.py...")
    connection_ok = test_jira_connection()
    if connection_ok:
        print("\nConnection Test Result (direct run): PASSED")

        print("\n--- Testing issue fetching (with changelog) ---")
        sample_jql = "project = MYPROJ ORDER BY created DESC" # !!! REPLACE MYPROJ !!!
        sample_fields = ["summary", "status", "issuetype", "created", "resolutiondate", "project"]
        
        print(f"Attempting to fetch issues with JQL: \"{sample_jql}\" including changelog.")
        issues_with_cl = fetch_issues_by_jql(
            jql_query=sample_jql, 
            fields=sample_fields, 
            max_issues_to_fetch=2, # Fetch only 2 for this test
            include_changelog=True
        )

        if issues_with_cl is not None:
            print(f"\nFetched {len(issues_with_cl)} issues successfully (changelog included):")
            for i, issue in enumerate(issues_with_cl):
                issue_fields = issue.get('fields', {})
                status_info = issue_fields.get('status', {})
                project_info = issue_fields.get('project', {})
                transitions = issue.get('status_transitions', [])
                print(f"  Issue {i+1}: Key={issue.get('key')}, "
                      f"Project={project_info.get('key', 'N/A')}, "
                      f"Status={status_info.get('name', 'N/A')}, "
                      f"Transitions: {len(transitions)}")
                if transitions:
                    for t_idx, tran in enumerate(transitions[:2]): # Print first 2 transitions
                        print(f"    └─ Tran {t_idx+1}: {tran['timestamp']} | {tran['from_status']} → {tran['to_status']}")
                    if len(transitions) > 2:
                        print("       ... and more transitions.")
            if not issues_with_cl:
                print("  No issues found matching the JQL query.")
        else:
            print("  Failed to fetch issues with changelog. Check logs.")

        print("\n--- Testing issue fetching (NO changelog) ---")
        issues_no_cl = fetch_issues_by_jql(
            jql_query=sample_jql,
            fields=sample_fields,
            max_issues_to_fetch=2,
            include_changelog=False
        )
        if issues_no_cl is not None:
            print(f"\nFetched {len(issues_no_cl)} issues successfully (changelog NOT included):")
            for i, issue in enumerate(issues_no_cl):
                 print(f"  Issue {i+1}: Key={issue.get('key')}, "
                       f"Status Transitions key present: {'status_transitions' in issue}, "
                       f"Transitions: {issue.get('status_transitions')}")
        else:
            print("  Failed to fetch issues without changelog. Check logs.")

    else:
        print("\nConnection Test Result (direct run): FAILED - Check logs.")
        print("  Skipping issue fetching test due to connection failure.")