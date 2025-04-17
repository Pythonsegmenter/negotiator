"""Tests for the data manager module."""

import json
import os
import pytest
import shutil
from pathlib import Path
from src.data_manager import (
    DATA_DIR,
    USER_DIR,
    ensure_data_dir,
    clear_data_dir,
    save_user_info,
    load_user_info,
    generate_id,
)

@pytest.fixture
def sample_user_info() -> dict:
    """Return sample user information for testing."""
    return {
        "id": generate_id(),
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
        shutil.rmtree(DATA_DIR)
    
    # Ensure it doesn't exist
    assert not DATA_DIR.exists()
    
    # Call the function and check that it now exists
    ensure_data_dir()
    assert DATA_DIR.exists()
    
    # Check that the subdirectories exist
    assert USER_DIR.exists()

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
    user_file = USER_DIR / f"{sample_user_info['id']}.json"
    assert user_file.exists()
    
    # Load the user info
    loaded_info = load_user_info(sample_user_info['id'])
    
    # Check that the loaded info matches the original
    assert loaded_info == sample_user_info
    
    # Clean up
    os.unlink(user_file)

def test_load_user_info_nonexistent() -> None:
    """Test loading user information when the file doesn't exist."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Generate a random ID that won't exist
    non_existent_id = generate_id()
    
    # Check that the file doesn't exist
    user_file = USER_DIR / f"{non_existent_id}.json"
    assert not user_file.exists()
    
    # Load the user info
    loaded_info = load_user_info(non_existent_id)
    
    # Check that None is returned
    assert loaded_info is None

def test_load_user_info_backward_compatibility(sample_user_info: dict) -> None:
    """Test backward compatibility for loading user info without ID."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Create a user file in the user directory
    user_file = USER_DIR / f"{sample_user_info['id']}.json"
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(sample_user_info, f, indent=2)
    
    # Load without specifying an ID
    loaded_info = load_user_info()
    
    # Check that the loaded info matches
    assert loaded_info == sample_user_info
    
    # Clean up
    os.unlink(user_file)
    
    # Now test the old file location fallback
    old_user_file = DATA_DIR / "user_info.json"
    old_user_info = {"activity": "Old activity"}
    
    with open(old_user_file, "w", encoding="utf-8") as f:
        json.dump(old_user_info, f, indent=2)
    
    # Load without specifying an ID
    loaded_info = load_user_info()
    
    # Check that the loaded info matches the old file
    assert loaded_info == old_user_info
    
    # Clean up
    os.unlink(old_user_file) 