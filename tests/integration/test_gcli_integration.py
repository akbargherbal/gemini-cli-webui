"""
Integration tests for GCLI subprocess integration

These tests require GCLI to be installed and configured
"""

import pytest
import subprocess


@pytest.mark.integration
def test_gcli_available():
    """Test that GCLI is installed and accessible"""
    try:
        result = subprocess.run(
            ['gemini', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
    except FileNotFoundError:
        pytest.skip("GCLI not installed")


@pytest.mark.integration
def test_gcli_non_interactive_mode():
    """Test GCLI non-interactive mode works"""
    try:
        result = subprocess.run(
            ['gemini', '--non-interactive'],
            input='What is 2+2?',
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0
        assert len(result.stdout) > 0
    except FileNotFoundError:
        pytest.skip("GCLI not installed")
