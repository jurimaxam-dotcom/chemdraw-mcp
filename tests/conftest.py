"""Pytest configuration for authentication tests.

This file sets up the test environment before any tests are run.
"""

import os
import sys

# Set up test environment BEFORE any imports
os.environ["CHEMDRAW_SECRET_KEY"] = "test-secret-key-for-testing-only-1234567890123456"
os.environ["CHEMDRAW_API_KEYS"] = "test-api-key-1,test-api-key-2"

# Ensure the project root is in the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pathlib import Path

# Clean up any existing test files
def pytest_configure(config):
    """Configure pytest."""
    # Create a temporary directory for test files
    test_dir = Path.home() / ".chemdraw-mcp-test"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Set test-specific environment
    os.environ["CHEMDRAW_CONFIG_DIR"] = str(test_dir)


def pytest_unconfigure(config):
    """Clean up after tests."""
    # Clean up test files
    test_dir = Path.home() / ".chemdraw-mcp-test"
    if test_dir.exists():
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
