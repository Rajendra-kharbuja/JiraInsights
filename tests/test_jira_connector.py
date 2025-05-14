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