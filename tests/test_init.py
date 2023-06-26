import pytest
import importlib
from importlib.metadata import PackageNotFoundError
import gull_api


def raise_package_not_found_error(name):
    raise PackageNotFoundError("Simulated PackageNotFoundError")


def test_package_not_found(monkeypatch):
    # Use monkeypatch to override importlib.metadata.version function to raise PackageNotFoundError
    monkeypatch.setattr('importlib.metadata.version', raise_package_not_found_error)
    
    # Reload gull_api to force re-execution of its __init__.py with the mocked version function
    importlib.reload(gull_api)
    
    # Check that __version__ is set to None when PackageNotFoundError is raised
    assert gull_api.__version__ is None
