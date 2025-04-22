"""Tests for the UserSimulator class."""

import os
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.user.user_simulator import UserSimulator


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    with patch("src.user.user_simulator.ChatOpenAI") as mock_chat_openai:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value.content = "This is a simulated user response"
        mock_chat_openai.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_messenger():
    """Create a mock CLIMessenger for testing."""
    with patch("src.user.user_simulator.CLIMessenger") as mock_cli_messenger:
        mock_instance = MagicMock()
        mock_instance.get_conversation_history.return_value = [
            {
                "sender": "assistant",
                "content": "Hello, what activity are you interested in?",
            }
        ]
        mock_cli_messenger.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def user_simulator(mock_llm, mock_messenger):
    """Create a UserSimulator instance for testing."""
    # Set up environment variables
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "test_model"

    # Create a UserSimulator instance
    user_id = str(uuid.uuid4())
    simulator = UserSimulator(user_id=user_id)

    # Return the simulator
    return simulator


def test_initialization(user_simulator):
    """Test that the UserSimulator initializes correctly."""
    assert user_simulator is not None
    assert user_simulator.user_id is not None
    assert user_simulator.simulation_profile == {}


def test_initialization_with_profile():
    """Test that the UserSimulator initializes correctly with a profile."""
    # Set up environment variables
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "test_model"

    # Create a test profile
    profile = {"activity": "hiking", "location": "Mount Batur", "participants": 4}

    # Create a UserSimulator instance with the profile
    with patch("src.user.user_simulator.ChatOpenAI"):
        with patch("src.user.user_simulator.CLIMessenger"):
            simulator = UserSimulator(
                user_id=str(uuid.uuid4()), simulation_profile=profile
            )

    # Check that the profile was set correctly
    assert simulator.simulation_profile == profile


def test_format_simulation_profile():
    """Test the _format_simulation_profile method."""
    # Set up environment variables
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "test_model"

    # Create a test profile
    profile = {
        "activity": "hiking",
        "location": "Mount Batur",
        "participants": 4,
        "preferences": {"difficulty": "moderate", "price_vs_value": "best_value"},
    }

    # Create a UserSimulator instance with the profile
    with patch("src.user.user_simulator.ChatOpenAI"):
        with patch("src.user.user_simulator.CLIMessenger"):
            simulator = UserSimulator(
                user_id=str(uuid.uuid4()), simulation_profile=profile
            )

    # Format the profile
    formatted_profile = simulator._format_simulation_profile()

    # Check that the formatting is correct
    assert "- activity: hiking" in formatted_profile
    assert "- location: Mount Batur" in formatted_profile
    assert "- participants: 4" in formatted_profile
    assert "- preferences:" in formatted_profile


def test_set_simulation_profile():
    """Test the set_simulation_profile method."""
    # Set up environment variables
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "test_model"

    # Create a UserSimulator instance
    with patch("src.user.user_simulator.ChatOpenAI"):
        with patch("src.user.user_simulator.CLIMessenger"):
            simulator = UserSimulator(user_id=str(uuid.uuid4()))

    # Check that the profile is empty initially
    assert simulator.simulation_profile == {}

    # Set a new profile
    new_profile = {
        "activity": "snorkeling",
        "location": "Nusa Penida",
        "participants": 2,
    }
    simulator.set_simulation_profile(new_profile)

    # Check that the profile was updated
    assert simulator.simulation_profile == new_profile


def test_process_and_respond(user_simulator, mock_messenger, mock_llm):
    """Test the process_and_respond method."""
    # Set up the mock messenger to return a conversation history with an assistant message
    mock_messenger.get_conversation_history.return_value = [
        {
            "sender": "assistant",
            "content": "Hello, what activity are you interested in?",
        }
    ]

    # Call process_and_respond
    user_simulator.process_and_respond()

    # Assert that the LLM was called
    mock_llm.invoke.assert_called_once()

    # Assert that a message was sent
    mock_messenger.send.assert_called_once_with(
        "This is a simulated user response", sender="user"
    )


def test_process_and_respond_no_assistant_message(
    user_simulator, mock_messenger, mock_llm
):
    """Test that process_and_respond does nothing if there's no assistant message."""
    # Set up the mock messenger to return a conversation history with no assistant message
    mock_messenger.get_conversation_history.return_value = [
        {"sender": "user", "content": "I want to go hiking."}
    ]

    # Call process_and_respond
    user_simulator.process_and_respond()

    # Assert that the LLM was not called
    mock_llm.invoke.assert_not_called()

    # Assert that no message was sent
    mock_messenger.send.assert_not_called()


def test_process_and_respond_empty_conversation(
    user_simulator, mock_messenger, mock_llm
):
    """Test that process_and_respond does nothing if the conversation is empty."""
    # Set up the mock messenger to return an empty conversation history
    mock_messenger.get_conversation_history.return_value = []

    # Call process_and_respond
    user_simulator.process_and_respond()

    # Assert that the LLM was not called
    mock_llm.invoke.assert_not_called()

    # Assert that no message was sent
    mock_messenger.send.assert_not_called()
