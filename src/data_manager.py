"""Data manager module for handling user information storage and data directory operations."""

import json
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List

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


def load_user_id() -> str:
    """Load the user id as the file name of the first user info file in the data directory"""
    user_files = list(USER_DIR.glob("*.json"))
    if not user_files:
        raise FileNotFoundError("No user info files found in the data directory")
    return user_files[0].stem


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


def load_user_info(user_id: str) -> Dict[str, Any]:
    """
    Load user information from a JSON file.

    Args:
        user_id: The ID of the user to load information for.

    Returns:
        Dictionary containing user information if file exists, None otherwise

    Raises:
        ValueError: If user_id is not provided
    """
    ensure_data_dir()

    if not user_id:
        raise ValueError("User ID is required")

    user_file = USER_DIR / f"{user_id}.json"
    if not user_file.exists():
        return {}

    with open(user_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_guide_info(guide_info: Dict[str, Any]) -> None:
    """
    Save guide information to a JSON file based on the guide's ID.

    Args:
        guide_info: Dictionary containing guide information
    """
    ensure_data_dir()

    # Get the guide ID from the guide_info dictionary
    guide_id = guide_info.get("id")
    if not guide_id:
        raise ValueError("Guide ID is required")

    # Create the file path
    guide_file = GUIDE_DIR / f"{guide_id}.json"

    with open(guide_file, "w", encoding="utf-8") as f:
        json.dump(guide_info, f, indent=2)


def load_guide_info(guide_id: str) -> Dict[str, Any]:
    """
    Load guide information from a JSON file.

    Args:
        guide_id: The ID of the guide to load information for.

    Returns:
        Dictionary containing guide information
    """
    ensure_data_dir()

    if guide_id:
        guide_file = GUIDE_DIR / f"{guide_id}.json"
        if not guide_file.exists():
            raise FileNotFoundError(f"Guide file {guide_file} not found")

        with open(guide_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise ValueError("Guide ID is required")


def load_all_guide_info() -> List[Dict[str, Any]]:
    """
    Load all guide information from JSON files.

    Returns:
        List of dictionaries containing all guide information
    """
    ensure_data_dir()

    guide_files = list(GUIDE_DIR.glob("*.json"))
    if not guide_files:
        return []

    guide_info_list = []
    for guide_file in guide_files:
        with open(guide_file, "r", encoding="utf-8") as f:
            guide_info_list.append(json.load(f))

    return guide_info_list


def save_conversation(conversation_id: str, conversation: List[Dict[str, str]]) -> None:
    """
    Save a conversation to a JSON file.

    Args:
        conversation_id: The ID of the conversation (equivalent to user_id or guide_id)
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
        conversation_id: The ID of the conversation (equivalent to user_id or guide_id)

    Returns:
        List of conversation messages if file exists, empty list otherwise
    """
    ensure_data_dir()

    conversation_file = CONVERSATION_DIR / f"{conversation_id}.json"

    if not conversation_file.exists():
        raise FileNotFoundError(f"Conversation file {conversation_file} not found")

    with open(conversation_file, "r", encoding="utf-8") as f:
        return json.load(f)
