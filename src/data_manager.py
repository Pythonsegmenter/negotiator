"""Data manager module for handling user information storage and data directory operations."""

import json
import os
import shutil
from pathlib import Path
from typing import Any, Dict, Optional

# Define paths
DATA_DIR = Path("data")
USER_INFO_FILE = DATA_DIR / "user_info.json"


def ensure_data_dir() -> None:
    """
    Ensure that the data directory exists.
    
    Creates the data directory if it doesn't exist.
    """
    DATA_DIR.mkdir(exist_ok=True)


def clear_data_dir() -> None:
    """
    Clear all files in the data directory.
    
    If the directory doesn't exist, it will be created.
    """
    if DATA_DIR.exists():
        # Remove all files in the directory
        for file_path in DATA_DIR.glob("*"):
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
    else:
        # Create the directory if it doesn't exist
        ensure_data_dir()


def save_user_info(user_info: Dict[str, Any]) -> None:
    """
    Save user information to the user_info.json file.
    
    Args:
        user_info: Dictionary containing user information
    """
    ensure_data_dir()
    
    with open(USER_INFO_FILE, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=2)


def load_user_info() -> Optional[Dict[str, Any]]:
    """
    Load user information from the user_info.json file.
    
    Returns:
        Dictionary containing user information if file exists, None otherwise
    """
    if not USER_INFO_FILE.exists():
        return None
    
    with open(USER_INFO_FILE, "r", encoding="utf-8") as f:
        return json.load(f) 