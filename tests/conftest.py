# tests/conftest.py
import os
import sys

# Add the project root directory to the Python path
# This allows tests to import modules from the 'src' directory
# and allows modules in 'src' to import modules from the project root (like config.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# You can also define fixtures here if needed later
