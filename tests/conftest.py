"""
Pytest configuration and fixtures
"""

import pytest
import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def app():
    """Create Flask app for testing"""
    from app.main import app as flask_app
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client"""
    return app.test_client()


@pytest.fixture
def safe_test_dir(tmp_path):
    """Create a safe temporary directory for testing"""
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    return test_dir
