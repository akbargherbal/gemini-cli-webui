"""
Unit tests for main Flask application
"""

import pytest


@pytest.mark.unit
def test_index_route(client):
    """Test that index route loads"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'GCLI Web UI' in response.data


@pytest.mark.unit
def test_is_safe_directory():
    """Test directory validation logic"""
    from app.main import is_safe_directory
    import os
    
    # Should allow home directory
    home = os.path.expanduser('~')
    assert is_safe_directory(home) is True
    
    # Should block system directories
    assert is_safe_directory('/usr') is False
    assert is_safe_directory('/etc') is False
    assert is_safe_directory('/') is False
