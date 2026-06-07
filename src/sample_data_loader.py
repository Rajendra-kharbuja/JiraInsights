# src/sample_data_loader.py
# Loads committed Jira-like sample data for offline demo and test workflows.

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import config


class SampleDataError(ValueError):
    """Raised when offline sample data cannot be loaded or validated."""


def _default_sample_path() -> Path:
    project_root = Path(__file__).resolve().parents[1]
    return project_root / config.DEFAULT_SAMPLE_DATA_PATH


def load_sample_issues(sample_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Loads Jira-like sample issues from JSON for offline metric processing.

    Args:
        sample_path: Optional path to a JSON file. Defaults to the committed
            demo dataset configured in config.DEFAULT_SAMPLE_DATA_PATH.

    Returns:
        A deep-copied list of issue dictionaries.

    Raises:
        SampleDataError: If the file is missing, invalid JSON, or not a list of
            issue dictionaries.
    """
    data_path = Path(sample_path) if sample_path else _default_sample_path()

    try:
        with data_path.open(encoding="utf-8") as sample_file:
            loaded_data = json.load(sample_file)
    except FileNotFoundError as exc:
        raise SampleDataError(f"Sample data file not found: {data_path}") from exc
    except json.JSONDecodeError as exc:
        raise SampleDataError(f"Sample data file is not valid JSON: {data_path}") from exc

    if not isinstance(loaded_data, list):
        raise SampleDataError("Sample data must be a JSON list of Jira issue objects.")

    for index, issue in enumerate(loaded_data):
        if not isinstance(issue, dict):
            raise SampleDataError(
                f"Sample data item at index {index} must be a Jira issue object."
            )
        if not issue.get("key"):
            raise SampleDataError(
                f"Sample data item at index {index} is missing required 'key'."
            )

    return copy.deepcopy(loaded_data)
