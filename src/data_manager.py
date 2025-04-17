"""Data manager module for handling user information storage and data directory operations."""

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, List

# Define paths
DATA_DIR = Path("data")
USER_DIR = DATA_DIR / "users"
GUIDE_DIR = DATA_DIR / "guides"
CONVERSATION_DIR = DATA_DIR / "conversations"

def generate_id() -> str:
    """
    Generate a unique identifier.
    
    Returns:
        str: A unique UUID
    """
    return str(uuid.uuid4())

def ensure_data_dir() -> None:
    """
    Ensure that the data directory exists.
    
    Creates the data directory and its subdirectories if they don't exist.
    """
    DATA_DIR.mkdir(exist_ok=True)
    USER_DIR.mkdir(exist_ok=True)
    GUIDE_DIR.mkdir(exist_ok=True)
    CONVERSATION_DIR.mkdir(exist_ok=True)

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
    
    # Recreate the directories
    ensure_data_dir()

def save_user_info(user_info: Dict[str, Any]) -> None:
    """
    Save user information to a JSON file based on the user's ID.
    
    Args:
        user_info: Dictionary containing user information
    """
    ensure_data_dir()
    
    # Get the user ID from the user_info dictionary
    user_id = user_info.get("id")
    if not user_id:
        raise ValueError("User ID is required")
    
    # Create the file path
    user_file = USER_DIR / f"{user_id}.json"
    
    with open(user_file, "w", encoding="utf-8") as f:
        json.dump(user_info, f, indent=2)

def load_user_info(user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load user information from a JSON file.
    
    Args:
        user_id: The ID of the user to load information for.
               If None, loads the first user file found (for backward compatibility).
    
    Returns:
        Dictionary containing user information if file exists, None otherwise
    """
    ensure_data_dir()
    
    if user_id:
        user_file = USER_DIR / f"{user_id}.json"
        if not user_file.exists():
            return None
            
        with open(user_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Backward compatibility: load the first user file found
        user_files = list(USER_DIR.glob("*.json"))
        if not user_files:
            # Try the old location as a fallback
            old_user_file = DATA_DIR / "user_info.json"
            if old_user_file.exists():
                with open(old_user_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
            
        with open(user_files[0], "r", encoding="utf-8") as f:
            return json.load(f)

def save_conversation(conversation_id: str, conversation: List[Dict[str, str]]) -> None:
    """
    Save a conversation to a JSON file.
    
    Args:
        conversation_id: The ID of the conversation
        conversation: List of conversation messages
    """
    ensure_data_dir()
    
    conversation_file = CONVERSATION_DIR / f"{conversation_id}.json"
    
    with open(conversation_file, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=2)

def load_conversation(conversation_id: str) -> List[Dict[str, str]]:
    """
    Load a conversation from a JSON file.
    
    Args:
        conversation_id: The ID of the conversation
    
    Returns:
        List of conversation messages if file exists, empty list otherwise
    """
    ensure_data_dir()
    
    conversation_file = CONVERSATION_DIR / f"{conversation_id}.json"
    
    if not conversation_file.exists():
        return []
        
    with open(conversation_file, "r", encoding="utf-8") as f:
        return json.load(f) 