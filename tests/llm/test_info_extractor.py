"""Tests for the information extraction module."""

import pytest
from typing import Dict, Any, List, Optional
import json
from unittest.mock import patch

from src.user_manager import UserInfo
from src.llm.info_extractor import generate_info_extraction_prompt, extract_user_info_from_response
from src.llm.service import LLMService


def test_generate_info_extraction_prompt_with_existing_info() -> None:
    """Test prompt generation with existing user information."""
    # Arrange
    user_info = UserInfo(
        activity="Climb Mt Agung at sunrise",
        location="Mount Agung, Bali",
        start_time="2025-08-14T23:00+08:00",
        deadline_negotation="2025-05-10T18:00+02:00",
        participants=2,
        budget=300.0,
        preferences={"price_vs_value": "lowest_price"}
    )
    
    conversation_history = [
        {"sender": "agent", "text": "Hello, I'm Trippy. What are your travel plans?"},
        {"sender": "user", "text": "I'd like to climb Mt Agung in Bali at sunrise."},
        {"sender": "agent", "text": "Great! How many people will be participating?"},
        {"sender": "user", "text": "Just me and my partner, so 2 people."}
    ]
    
    # Act
    prompt = generate_info_extraction_prompt(user_info, conversation_history)
    
    # Assert
    assert "Current User Information" in prompt
    assert "Climb Mt Agung at sunrise" in prompt
    assert "2025-08-14T23:00+08:00" in prompt
    assert "Conversation History" in prompt
    assert "agent: Hello, I'm Trippy" in prompt
    assert "user: I'd like to climb Mt Agung" in prompt


def test_generate_info_extraction_prompt_with_no_info() -> None:
    """Test prompt generation with no existing user information."""
    # Arrange
    conversation_history = [
        {"sender": "agent", "text": "Hello, I'm Trippy. What are your travel plans?"},
        {"sender": "user", "text": "I want to go scuba diving in Bali."}
    ]
    
    # Act
    prompt = generate_info_extraction_prompt(None, conversation_history)
    
    # Assert
    assert "Current User Information" in prompt
    assert "{}" in prompt  # Empty JSON for no current info
    assert "agent: Hello, I'm Trippy" in prompt
    assert "user: I want to go scuba diving in Bali" in prompt


def test_extract_user_info_from_response_with_new_info() -> None:
    """Test extracting user info from a valid LLM response with new information."""
    # Arrange
    llm_response = json.dumps({
        "found_new_info": True,
        "new_info": {
            "activity": "Scuba diving",
            "location": "Tulamben, Bali"
        },
        "reasoning": "User mentioned wanting to go scuba diving in Bali."
    })
    
    # Act
    found_new_info, new_info, reasoning = extract_user_info_from_response(llm_response)
    
    # Assert
    assert found_new_info is True
    assert new_info["activity"] == "Scuba diving"
    assert new_info["location"] == "Tulamben, Bali"
    assert "User mentioned" in reasoning


def test_extract_user_info_from_response_with_no_new_info() -> None:
    """Test extracting user info from a valid LLM response with no new information."""
    # Arrange
    llm_response = json.dumps({
        "found_new_info": False,
        "new_info": {},
        "reasoning": "No new information detected in the conversation."
    })
    
    # Act
    found_new_info, new_info, reasoning = extract_user_info_from_response(llm_response)
    
    # Assert
    assert found_new_info is False
    assert new_info == {}
    assert "No new information" in reasoning


def test_extract_user_info_from_response_with_invalid_json() -> None:
    """Test extracting user info from an invalid LLM response."""
    # Arrange
    llm_response = "This is not valid JSON"
    
    # Act
    found_new_info, new_info, reasoning = extract_user_info_from_response(llm_response)
    
    # Assert
    assert found_new_info is False
    assert new_info == {}
    assert "Failed to parse" in reasoning


@patch('src.llm.service.LLMService._send_prompt_to_llm')
def test_llm_service_extract_user_info(mock_send_prompt) -> None:
    """Test the LLM service's extract_user_info method."""
    # Arrange
    mock_send_prompt.return_value = json.dumps({
        "found_new_info": True,
        "new_info": {
            "budget": 500,
            "participants": 3
        },
        "reasoning": "User updated their budget to $500 and changed participants from 2 to 3."
    })
    
    user_info = UserInfo(
        activity="Climb Mt Agung at sunrise",
        location="Mount Agung, Bali",
        start_time="2025-08-14T23:00+08:00",
        deadline_negotation="2025-05-10T18:00+02:00",
        participants=2,
        budget=300.0,
        preferences={"price_vs_value": "lowest_price"}
    )
    
    conversation_history = [
        {"sender": "agent", "text": "What's your budget for this activity?"},
        {"sender": "user", "text": "I can spend up to $500."},
        {"sender": "agent", "text": "And how many people will be joining?"},
        {"sender": "user", "text": "Actually, there will be 3 of us now."}
    ]
    
    llm_service = LLMService()
    
    # Act
    found_new_info, new_info, reasoning = llm_service.extract_user_info(
        user_info, conversation_history
    )
    
    # Assert
    assert found_new_info is True
    assert new_info["budget"] == 500
    assert new_info["participants"] == 3
    assert "User updated their budget" in reasoning
    # Verify the mock was called with a prompt containing the current info
    assert mock_send_prompt.called
    prompt_arg = mock_send_prompt.call_args[0][0]
    assert "Current User Information" in prompt_arg
    assert "Climb Mt Agung at sunrise" in prompt_arg 