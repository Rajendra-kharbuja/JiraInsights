# src/jira_connector.py
# Handles connection and data fetching from the Jira API using Basic Authentication.

import os
import sys # For diagnostic print
import requests
import logging
from dotenv import load_dotenv, find_dotenv # Added find_dotenv
from typing import Optional, Tuple

# Diagnostic print for sys.path when this module is loaded
print(f"DEBUG [jira_connector.py]: sys.path at import time = {sys.path}")
try:
    import config
    print("DEBUG [jira_connector.py]: Successfully imported 'config'.")
except ModuleNotFoundError as e:
    print(f"ERROR [jira_connector.py]: Failed to import 'config'. Error: {e}")
    raise # Re-raise the error to make it clear

# Basic logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

def load_credentials() -> Optional[Tuple[str, str, str]]:
    """
    Loads Jira URL, email, and password from the .env file.

    Returns:
        A tuple containing (jira_url, jira_email, jira_password) if all are found,
        otherwise None.
    """
    # Load environment variables from .env file found in project root or parent directories
    # find_dotenv() helps locate the .env file correctly, especially when run from subdirs
    env_path = find_dotenv(raise_error_if_not_found=False)
    if env_path:
        print(f"DEBUG [jira_connector.py]: Loading .env from: {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        print("DEBUG [jira_connector.py]: .env file not found by find_dotenv(). Relying on os.getenv directly.")
        # If .env is not found, os.getenv will still check environment if variables are set externally

    jira_url = os.getenv("JIRA_URL")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_password = os.getenv("JIRA_PASSWORD") # Using password directly

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
            logging.error(f"HTTP Error: Received status code {status_code} from Jira. Details: {e}")
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

if __name__ == "__main__":
    print("Running Jira connection test directly from jira_connector.py...")
    if test_jira_connection():
        print("\nConnection Test Result (direct run): PASSED")
    else:
        print("\nConnection Test Result (direct run): FAILED - Check logs.")