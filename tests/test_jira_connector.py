# tests/test_jira_connector.py
# Unit tests for the Jira API interaction logic in src/jira_connector.py.
# Uses pytest, unittest.mock, and requests_mock.

import sys
print(f"DEBUG [test_jira_connector.py]: sys.path at import time = {sys.path}")

import pytest
from unittest.mock import patch, MagicMock
import os
import logging # Import logging for caplog.set_level
import requests # <--- ADDED THIS IMPORT
import base64 # <--- ADDED THIS IMPORT

# Import the module and config to be tested/used
try:
    from src import jira_connector
    import config
    print("DEBUG [test_jira_connector.py]: Successfully imported 'src.jira_connector' and 'config'.")
except ModuleNotFoundError as e:
    print(f"ERROR [test_jira_connector.py]: Failed to import modules. Error: {e}")
    print(f"Current sys.path: {sys.path}")
    raise

# --- Tests for load_credentials ---
# (No changes to these tests)
@patch('src.jira_connector.load_dotenv')
@patch('os.getenv')
def test_load_credentials_success(mock_os_getenv, mock_load_dotenv_call):
    """ Test loading credentials successfully when all env vars are set """
    mock_os_getenv.side_effect = lambda key: {
        "JIRA_URL": "https://test.atlassian.net/",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_PASSWORD": "test_password"
    }.get(key)
    with patch('src.jira_connector.find_dotenv', return_value='/fake/path/to/.env') as mock_find_dotenv_call:
        credentials = jira_connector.load_credentials()
    mock_find_dotenv_call.assert_called_once_with(raise_error_if_not_found=False)
    mock_load_dotenv_call.assert_called_once_with(dotenv_path='/fake/path/to/.env')
    assert credentials is not None
    assert credentials[0] == "https://test.atlassian.net"
    assert credentials[1] == "test@example.com"
    assert credentials[2] == "test_password"

@patch('src.jira_connector.load_dotenv')
@patch('os.getenv')
def test_load_credentials_missing_var(mock_os_getenv, mock_load_dotenv_call, caplog):
    """ Test loading credentials when one environment variable is missing """
    mock_os_getenv.side_effect = lambda key: {
        "JIRA_URL": "https://test.atlassian.net",
        "JIRA_EMAIL": "test@example.com",
    }.get(key)
    with patch('src.jira_connector.find_dotenv', return_value=None):
        credentials = jira_connector.load_credentials()
    assert credentials is None
    assert "JIRA_PASSWORD not found" in caplog.text
    assert "Missing one or more required Jira credentials" in caplog.text

@patch('src.jira_connector.load_dotenv')
@patch('os.getenv')
def test_load_credentials_invalid_url(mock_os_getenv, mock_load_dotenv_call, caplog):
    """ Test loading credentials with an invalid JIRA_URL format """
    mock_os_getenv.side_effect = lambda key: {
        "JIRA_URL": "invalid-url-format",
        "JIRA_EMAIL": "test@example.com",
        "JIRA_PASSWORD": "test_password"
    }.get(key)
    with patch('src.jira_connector.find_dotenv', return_value='/fake/path/to/.env'):
        credentials = jira_connector.load_credentials()
    assert credentials is None
    assert "Invalid JIRA_URL format" in caplog.text


# --- Tests for test_jira_connection ---

@patch('src.jira_connector.load_credentials')
def test_jira_connection_success(mock_load_credentials_call, requests_mock, caplog):
    """ Test successful Jira connection and authentication """
    mock_url = "https://test.atlassian.net"
    mock_email = "test@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    mock_response_data = {"displayName": "Test User"}
    requests_mock.get(test_api_url, json=mock_response_data, status_code=200)

    caplog.set_level(logging.INFO) # <--- ADDED THIS LINE to ensure INFO logs are captured
    result = jira_connector.test_jira_connection()

    assert result is True
    mock_load_credentials_call.assert_called_once()
    # Check the specific part of the log message we care about
    assert f"Attempting to connect to Jira at {mock_url}" in caplog.text
    assert f"Authenticated as: Test User ({mock_email})" in caplog.text
    # Verify Basic Authentication header
    assert requests_mock.called_once # Ensure the mock was called
    last_request = requests_mock.last_request
    assert last_request is not None # Should not be None if called_once is True
    
    # Construct the expected Basic Auth header
    auth_string = f"{mock_email}:{mock_password}"
    expected_auth_header = f"Basic {base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')}"
    
    assert 'Authorization' in last_request.headers
    assert last_request.headers['Authorization'] == expected_auth_header


@patch('src.jira_connector.load_credentials')
def test_jira_connection_auth_failure_401(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to 401 Unauthorized """
    mock_url = "https://test.atlassian.net"
    mock_email = "wrong@example.com"
    mock_password = "wrong_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    requests_mock.get(test_api_url, status_code=401, reason="Unauthorized")
    
    caplog.set_level(logging.ERROR) # Ensure ERROR logs are captured
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "Authentication Failed (401 Unauthorized)" in caplog.text
    assert f"Invalid email or password for user '{mock_email}'" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_forbidden_403(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to 403 Forbidden """
    mock_url = "https://test.atlassian.net"
    mock_email = "no_perms@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    requests_mock.get(test_api_url, status_code=403, reason="Forbidden")

    caplog.set_level(logging.ERROR)
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "Authorization Failed (403 Forbidden)" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_not_found_404(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to 404 Not Found """
    mock_url = "https://test.atlassian.net"
    mock_email = "test@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    requests_mock.get(test_api_url, status_code=404, reason="Not Found")

    caplog.set_level(logging.ERROR)
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "API Endpoint Not Found (404)" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_server_error_500(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to 500 Internal Server Error """
    mock_url = "https://test.atlassian.net"
    mock_email = "test@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    requests_mock.get(test_api_url, status_code=500, reason="Internal Server Error")

    caplog.set_level(logging.ERROR)
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "HTTP Error: Received status code 500" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_connection_error(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to requests.exceptions.ConnectionError """
    mock_url = "https://nonexistent-jira-instance.com"
    mock_email = "test@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    # Use the imported requests module here
    requests_mock.get(test_api_url, exc=requests.exceptions.ConnectionError("Failed to establish connection"))

    caplog.set_level(logging.ERROR)
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "Connection Error: Failed to connect to Jira URL" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_timeout(mock_load_credentials_call, requests_mock, caplog):
    """ Test connection failure due to requests.exceptions.Timeout """
    mock_url = "https://slow-jira.com"
    mock_email = "test@example.com"
    mock_password = "test_password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    test_api_url = f"{mock_url}{config.JIRA_API_MYSELF_PATH}"
    # Use the imported requests module here
    requests_mock.get(test_api_url, exc=requests.exceptions.Timeout("Request timed out"))

    caplog.set_level(logging.ERROR)
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "Request Timeout: The request to Jira timed out" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_jira_connection_missing_credentials_prevents_call(mock_load_credentials_call, caplog):
    """ Test test_jira_connection when load_credentials returns None """
    mock_load_credentials_call.return_value = None

    caplog.set_level(logging.INFO) # Set to capture potential INFO logs if any were made
    result = jira_connector.test_jira_connection()

    assert result is False
    assert "Attempting to connect to Jira" not in caplog.text
# --- Tests for fetch_issues_by_jql ---

@patch('src.jira_connector.load_credentials')
def test_fetch_issues_single_page_success(mock_load_credentials_call, requests_mock, caplog):
    """Test fetching issues that fit on a single page."""
    mock_url = "https://test.jira.com"
    mock_email = "user@test.com"
    mock_password = "password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    jql = "project = TEST"
    expected_fields_str = "id,key,issuetype,status,created,resolutiondate" # Default fields
    search_url_matcher = f"{mock_url}{config.JIRA_API_SEARCH_PATH}"

    mock_response = {
        "startAt": 0,
        "maxResults": 50,
        "total": 2,
        "issues": [
            {"id": "1", "key": "TEST-1", "fields": {"summary": "Issue 1"}},
            {"id": "2", "key": "TEST-2", "fields": {"summary": "Issue 2"}},
        ]
    }
    requests_mock.get(search_url_matcher, json=mock_response, status_code=200)
    caplog.set_level(logging.INFO)
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues is not None
    assert len(issues) == 2
    assert issues[0]["key"] == "TEST-1"
    assert requests_mock.called_once
    
    # Debug print to see exactly what requests_mock captured
    print(f"DEBUG: Captured Query String from requests_mock: {requests_mock.last_request.qs}")

    assert requests_mock.last_request.qs['jql'][0].lower() == jql.lower() # Case-insensitive comparison
    assert requests_mock.last_request.qs['fields'] == [expected_fields_str]
    assert requests_mock.last_request.qs['startat'] == ['0'] # qs values are lists of strings
    assert "Successfully fetched a total of 2 issues." in caplog.text


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_multiple_pages_success(mock_load_credentials_call, requests_mock, caplog):
    """Test fetching issues that span multiple pages."""
    mock_url = "https://test.jira.com"
    mock_email = "user@test.com"
    mock_password = "password"
    mock_load_credentials_call.return_value = (mock_url, mock_email, mock_password)

    jql = "project = MULTI"
    search_url_matcher = f"{mock_url}{config.JIRA_API_SEARCH_PATH}"
    # Try to get the default max_results_per_page from the function, otherwise assume 50
    # This is a bit fragile as __defaults__ can be None if no defaults are set or if it's a builtin.
    # For fetch_issues_by_jql, 'fields' is the first default, 'max_issues_to_fetch' is the second.
    # The actual max_results_per_page is hardcoded to 50 inside the function for now.
    # So, for this test, we'll use the internally hardcoded value for consistency in calculation.
    internal_max_results_per_page = 50


    # Page 1: max_results_per_page items
    mock_response_p1 = {
        "startAt": 0, "maxResults": internal_max_results_per_page, "total": internal_max_results_per_page + 1,
        "issues": [{"id": str(i), "key": f"MULTI-{i}"} for i in range(1, internal_max_results_per_page + 1)]
    }
    # Page 2: 1 item
    mock_response_p2 = {
        "startAt": internal_max_results_per_page, "maxResults": internal_max_results_per_page, "total": internal_max_results_per_page + 1,
        "issues": [{"id": str(internal_max_results_per_page + 1), "key": f"MULTI-{internal_max_results_per_page + 1}"}]
    }

    requests_mock.get(search_url_matcher, [
        {'json': mock_response_p1, 'status_code': 200},
        {'json': mock_response_p2, 'status_code': 200},
    ])
    caplog.set_level(logging.INFO)
    issues = jira_connector.fetch_issues_by_jql(jql, max_issues_to_fetch=None)

    assert issues is not None
    assert len(issues) == internal_max_results_per_page + 1
    assert issues[0]["key"] == "MULTI-1"
    assert issues[-1]["key"] == f"MULTI-{internal_max_results_per_page + 1}"
    assert requests_mock.call_count == 2
    history = requests_mock.request_history
    assert history[1].qs['startat'] == [str(internal_max_results_per_page)]
    assert f"Successfully fetched a total of {internal_max_results_per_page + 1} issues." in caplog.text


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_empty_result(mock_load_credentials_call, requests_mock, caplog):
    """Test fetching when JQL returns no issues."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "status = Empty"
    mock_response = {"startAt": 0, "maxResults": 50, "total": 0, "issues": []}
    requests_mock.get(f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}", json=mock_response)
    
    caplog.set_level(logging.INFO)
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues == []
    assert "Successfully fetched a total of 0 issues." in caplog.text


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_with_custom_fields(mock_load_credentials_call, requests_mock):
    """Test fetching with a custom list of fields."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "project = CUSTOM"
    custom_fields = ["summary", "assignee", "reporter"]
    custom_fields_str = "summary,assignee,reporter"
    
    mock_response = {"startAt": 0, "maxResults": 50, "total": 1, "issues": [{"key": "CUSTOM-1"}]}
    requests_mock.get(f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}", json=mock_response)

    jira_connector.fetch_issues_by_jql(jql, fields=custom_fields)

    assert requests_mock.called_once
    assert requests_mock.last_request.qs['fields'] == [custom_fields_str]


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_http_error(mock_load_credentials_call, requests_mock, caplog):
    """Test handling of HTTP error during JQL search."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "project = ERROR"
    requests_mock.get(f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}", status_code=400, text="Bad JQL")

    caplog.set_level(logging.ERROR)
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues is None
    assert "HTTP Error during JQL search" in caplog.text
    assert "400 - Bad JQL" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_request_exception(mock_load_credentials_call, requests_mock, caplog):
    """Test handling of a generic RequestException."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "project = CONN_ERROR"
    requests_mock.get(f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}", exc=requests.exceptions.ConnectionError("Network down"))

    caplog.set_level(logging.ERROR)
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues is None
    assert "Request Exception during JQL search" in caplog.text
    assert "Network down" in caplog.text


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_pagination_stops_at_max_issues(mock_load_credentials_call, requests_mock, caplog):
    """Test that pagination stops when max_issues_to_fetch is reached."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "project = LIMIT"
    search_url_matcher = f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}"
    limit = 3
    internal_max_results_per_page = 2 # To force pagination and test slicing

    # Page 1
    mock_response_p1 = {
        "startAt": 0, "maxResults": internal_max_results_per_page, "total": 10,
        "issues": [{"id": "1"}, {"id": "2"}]
    }
    # Page 2 (server returns 2, but we only need 1 more to reach limit of 3)
    mock_response_p2 = {
        "startAt": internal_max_results_per_page, "maxResults": internal_max_results_per_page, "total": 10,
        "issues": [{"id": "3"}, {"id": "4"}] 
    }
    
    requests_mock.get(search_url_matcher, [
        {'json': mock_response_p1, 'status_code': 200},
        {'json': mock_response_p2, 'status_code': 200} 
    ])
    caplog.set_level(logging.INFO)
    issues = jira_connector.fetch_issues_by_jql(jql, max_issues_to_fetch=limit)

    assert issues is not None
    assert len(issues) == limit
    assert issues[0]["id"] == "1"
    assert issues[1]["id"] == "2"
    assert issues[2]["id"] == "3" 
    assert f"Reached configured max_issues_to_fetch ({limit})" in caplog.text
    assert requests_mock.call_count == 2 # Fetches page 1 (2 issues), then page 2 (2 issues), then slices to 3.


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_pagination_stops_if_page_empty(mock_load_credentials_call, requests_mock, caplog):
    """Test pagination stops if a page returns no issues, even if total suggests more."""
    mock_load_credentials_call.return_value = ("https://test.jira.com", "user", "pass")
    jql = "project = EMPTY_PAGE"
    search_url_matcher = f"https://test.jira.com{config.JIRA_API_SEARCH_PATH}"
    internal_max_results_per_page = 2

    mock_response_p1 = {
        "startAt": 0, "maxResults": internal_max_results_per_page, "total": 10, # Server says 10 total
        "issues": [{"id": "1"}, {"id": "2"}]
    }
    mock_response_p2 = { # This page is unexpectedly empty
        "startAt": internal_max_results_per_page, "maxResults": internal_max_results_per_page, "total": 10,
        "issues": []
    }
    requests_mock.get(search_url_matcher, [
        {'json': mock_response_p1, 'status_code': 200},
        {'json': mock_response_p2, 'status_code': 200},
    ])
    caplog.set_level(logging.INFO)
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues is not None
    assert len(issues) == 2 # Only issues from the first page
    assert "No more issues returned on current page. Pagination complete." in caplog.text
    assert requests_mock.call_count == 2


@patch('src.jira_connector.load_credentials')
def test_fetch_issues_no_credentials(mock_load_credentials_call, caplog):
    """Test fetch_issues_by_jql when load_credentials returns None."""
    mock_load_credentials_call.return_value = None 
    jql = "project = TEST"
    
    # load_credentials itself logs an error if it fails.
    # We are checking that fetch_issues_by_jql doesn't proceed.
    caplog.set_level(logging.INFO) # To check if "Initiating JQL search" is NOT logged
    
    issues = jira_connector.fetch_issues_by_jql(jql)

    assert issues is None
    assert "Initiating JQL search" not in caplog.text
    # Verify that load_credentials was called
    mock_load_credentials_call.assert_called_once()