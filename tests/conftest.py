# tests/conftest.py
import sys
import os

print("INFO [conftest.py]: conftest.py is being executed.")

# Add the project root directory to the Python path
# This allows tests to import modules from the 'src' directory
# and allows modules in 'src' to import modules from the project root (like config.py)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f"INFO [conftest.py]: Added '{project_root}' to sys.path.")
else:
    print(f"INFO [conftest.py]: '{project_root}' was already in sys.path.")

print(f"INFO [conftest.py]: Current sys.path entries relevant to project (first few and project_root if found):")
for i, path_entry in enumerate(sys.path[:5]): # Print first 5 entries
    print(f"  sys.path[{i}]: {path_entry}")
if project_root in sys.path:
    print(f"  Confirmed: '{project_root}' is in sys.path at index {sys.path.index(project_root)}.")
else:
    print(f"  WARNING: '{project_root}' IS NOT in sys.path after attempting to add it.")

# You can also define fixtures here if needed later