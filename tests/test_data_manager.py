"""Tests for the data manager module."""

import json
import os
import pytest
from pathlib import Path
from src.data_manager import (
    DATA_DIR,
    USER_INFO_FILE,
    ensure_data_dir,
    clear_data_dir,
    save_user_info,
    load_user_info,
)

@pytest.fixture
def sample_user_info() -> dict:
    """Return sample user information for testing."""
    return {
        "activity": "Climb Mt. Fuji",
        "location": "Mount Fuji, Japan",
        "start_time": "2023-07-15T08:00:00+09:00",
        "deadline_negotation": "2023-06-30T23:59:59+09:00",
        "participants": 3,
        "budget": 1500.0,
        "preferences": {"price_vs_value": "best_value"}
    }

def test_ensure_data_dir() -> None:
    """Test that ensure_data_dir creates the data directory."""
    # Remove the directory if it exists
    if DATA_DIR.exists():
        for file_path in DATA_DIR.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        DATA_DIR.rmdir()
    
    # Ensure it doesn't exist
    assert not DATA_DIR.exists()
    
    # Call the function and check that it now exists
    ensure_data_dir()
    assert DATA_DIR.exists()

def test_clear_data_dir() -> None:
    """Test that clear_data_dir removes all files but keeps the directory."""
    # Ensure the directory exists
    ensure_data_dir()
    
    # Create a test file
    test_file = DATA_DIR / "test_file.txt"
    with open(test_file, "w") as f:
        f.write("Test content")
    
    # Check that the file exists
    assert test_file.exists()
    
    # Clear the directory
    clear_data_dir()
    
    # Check that the directory still exists but the file is gone
    assert DATA_DIR.exists()
    assert not test_file.exists()

def test_save_and_load_user_info(sample_user_info: dict) -> None:
    """Test saving and loading user information."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Save user info
    save_user_info(sample_user_info)
    
    # Check that the file exists
    assert USER_INFO_FILE.exists()
    
    # Load the user info
    loaded_info = load_user_info()
    
    # Check that the loaded info matches the original
    assert loaded_info == sample_user_info

def test_load_user_info_nonexistent() -> None:
    """Test loading user information when the file doesn't exist."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Check that the file doesn't exist
    assert not USER_INFO_FILE.exists()
    
    # Load the user info
    loaded_info = load_user_info()
    
    # Check that None is returned
    assert loaded_info is None 