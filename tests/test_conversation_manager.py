"""Tests for the conversation management functions in the data manager module."""

import json
import os
import pytest
from pathlib import Path
from typing import List, Dict

from src.data_manager import (
    DATA_DIR,
    CONVERSATION_DIR,
    ensure_data_dir,
    clear_data_dir,
    generate_id,
    save_conversation,
    load_conversation,
)

@pytest.fixture
def sample_conversation() -> List[Dict[str, str]]:
    """Return sample conversation for testing."""
    return [
        {"sender": "assistant", "text": "Hello, how can I help you?"},
        {"sender": "user", "text": "I need help with my trip"},
        {"sender": "assistant", "text": "What kind of trip are you planning?"}
    ]

@pytest.fixture
def test_conversation_id() -> str:
    """Return a test conversation ID."""
    return generate_id()

def test_generate_id() -> None:
    """Test that generate_id returns a UUID string."""
    id1 = generate_id()
    id2 = generate_id()
    
    # Check that IDs are strings
    assert isinstance(id1, str)
    assert isinstance(id2, str)
    
    # Check that IDs are different
    assert id1 != id2
    
    # Check that IDs have the UUID format (including hyphens)
    assert len(id1) == 36
    assert len(id2) == 36

def test_ensure_conversation_dir() -> None:
    """Test that the conversation directory is created."""
    # First make sure the data directory exists
    ensure_data_dir()
    
    # Check that the conversation directory exists
    assert CONVERSATION_DIR.exists()
    assert CONVERSATION_DIR.is_dir()

def test_save_and_load_conversation(sample_conversation: List[Dict[str, str]], test_conversation_id: str) -> None:
    """Test saving and loading a conversation."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Save the conversation
    save_conversation(test_conversation_id, sample_conversation)
    
    # Check that the file exists
    conversation_file = CONVERSATION_DIR / f"{test_conversation_id}.json"
    assert conversation_file.exists()
    
    # Load the conversation
    loaded_conversation = load_conversation(test_conversation_id)
    
    # Check that the loaded conversation matches the original
    assert loaded_conversation == sample_conversation
    
    # Clean up
    os.unlink(conversation_file)

def test_load_nonexistent_conversation(test_conversation_id: str) -> None:
    """Test loading a conversation that doesn't exist."""
    # Ensure the directory is clean
    clear_data_dir()
    
    # Check that the file doesn't exist
    conversation_file = CONVERSATION_DIR / f"{test_conversation_id}.json"
    assert not conversation_file.exists()
    
    # Load the conversation
    loaded_conversation = load_conversation(test_conversation_id)
    
    # Check that an empty list is returned
    assert loaded_conversation == []

def test_save_conversation_creates_directory() -> None:
    """Test that save_conversation creates the directory if it doesn't exist."""
    # Remove the conversation directory if it exists
    if CONVERSATION_DIR.exists():
        for file_path in CONVERSATION_DIR.glob("*"):
            if file_path.is_file():
                file_path.unlink()
        CONVERSATION_DIR.rmdir()
    
    # Ensure it doesn't exist
    assert not CONVERSATION_DIR.exists()
    
    # Save a conversation
    test_id = generate_id()
    save_conversation(test_id, [{"sender": "assistant", "text": "Test"}])
    
    # Check that the directory was created
    assert CONVERSATION_DIR.exists()
    
    # Clean up
    conversation_file = CONVERSATION_DIR / f"{test_id}.json"
    os.unlink(conversation_file) 