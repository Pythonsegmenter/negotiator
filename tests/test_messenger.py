"""Tests for the messenger module."""

import os
from unittest.mock import patch

import pytest

from src.data_manager import (
    CONVERSATION_DIR,
    generate_id,
    load_conversation,
    save_conversation,
)
from src.messenger.cli import CLIMessenger


@pytest.fixture
def mock_input():
    """Fixture to mock the input function."""
    with patch("builtins.input", return_value="Test user input") as mock:
        yield mock


@pytest.fixture
def mock_print():
    """Fixture to mock the print function."""
    with patch("builtins.print") as mock:
        yield mock


@pytest.fixture
def test_conversation_id():
    """Fixture to provide a test conversation ID."""
    return generate_id()


@pytest.fixture
def sample_conversation():
    """Fixture to provide a sample conversation history."""
    return [
        {"sender": "assistant", "text": "Hello, how can I help you?"},
        {"sender": "user", "text": "I need help with my trip"},
        {"sender": "assistant", "text": "What kind of trip are you planning?"},
    ]


@pytest.fixture
def cleanup_test_conversation(test_conversation_id):
    """Fixture to clean up test conversation file after test."""
    yield
    # Cleanup after test
    conversation_file = CONVERSATION_DIR / f"{test_conversation_id}.json"
    if conversation_file.exists():
        os.unlink(conversation_file)


def test_init_without_id():
    """Test initializing a messenger without a conversation ID."""
    messenger = CLIMessenger()
    assert messenger.conversation_id is None
    assert messenger.conversation_history == []


def test_init_with_id(test_conversation_id, cleanup_test_conversation):
    """Test initializing a messenger with a conversation ID."""
    # First, create a conversation file
    sample_convo = [{"sender": "assistant", "text": "Test message"}]
    save_conversation(test_conversation_id, sample_convo)

    # Now initialize with the ID
    messenger = CLIMessenger(test_conversation_id)

    # Check that the conversation was loaded
    assert messenger.conversation_id == test_conversation_id
    assert messenger.conversation_history == sample_convo


def test_send_without_id(mock_print):
    """Test sending a message without a conversation ID."""
    messenger = CLIMessenger()
    test_message = "Test message"

    messenger.send(test_message)

    # Check that print was called with the message
    mock_print.assert_called_once_with(test_message)

    # Check that the message was added to conversation history
    assert len(messenger.conversation_history) == 1
    assert messenger.conversation_history[0] == {
        "sender": "assistant",
        "text": test_message,
    }


def test_send_with_id(mock_print, test_conversation_id, cleanup_test_conversation):
    """Test sending a message with a conversation ID."""
    messenger = CLIMessenger(test_conversation_id)
    test_message = "Test message"

    messenger.send(test_message)

    # Check that print was called with the message
    mock_print.assert_called_once_with(test_message)

    # Check that the message was added to conversation history
    assert len(messenger.conversation_history) == 1
    assert messenger.conversation_history[0] == {
        "sender": "assistant",
        "text": test_message,
    }

    # Check that the conversation was saved
    loaded_convo = load_conversation(test_conversation_id)
    assert loaded_convo == messenger.conversation_history


def test_receive_without_id(mock_input):
    """Test receiving a message without a conversation ID."""
    messenger = CLIMessenger()
    expected_input = "Test user input"  # This matches our mock

    # Test with default empty prompt
    result = messenger.receive()

    # Check that input was called
    mock_input.assert_called_once_with("")

    # Check that the result is what we expected
    assert result == expected_input

    # Check that the message was added to conversation history
    assert len(messenger.conversation_history) == 1
    assert messenger.conversation_history[0] == {
        "sender": "user",
        "text": expected_input,
    }


def test_receive_with_prompt(mock_input):
    """Test receiving a message with a custom prompt."""
    messenger = CLIMessenger()
    prompt = "Please enter your response: "

    result = messenger.receive(prompt)

    # Check that input was called with our prompt
    mock_input.assert_called_once_with(prompt)

    # The result should be from our mock
    assert result == "Test user input"


def test_receive_with_id(mock_input, test_conversation_id, cleanup_test_conversation):
    """Test receiving a message with a conversation ID."""
    messenger = CLIMessenger(test_conversation_id)
    expected_input = "Test user input"  # This matches our mock

    messenger.receive()

    # Check that the message was added to conversation history
    assert len(messenger.conversation_history) == 1
    assert messenger.conversation_history[0] == {
        "sender": "user",
        "text": expected_input,
    }

    # Check that the conversation was saved
    loaded_convo = load_conversation(test_conversation_id)
    assert loaded_convo == messenger.conversation_history


def test_get_conversation_history(sample_conversation):
    """Test getting the conversation history."""
    messenger = CLIMessenger()
    messenger.conversation_history = sample_conversation.copy()

    result = messenger.get_conversation_history()

    assert result == sample_conversation


def test_get_formatted_conversation(sample_conversation):
    """Test getting the formatted conversation."""
    messenger = CLIMessenger()
    messenger.conversation_history = sample_conversation.copy()

    result = messenger.get_formatted_conversation()

    expected = "\n".join(
        [
            "assistant: Hello, how can I help you?",
            "user: I need help with my trip",
            "assistant: What kind of trip are you planning?",
        ]
    )

    assert result == expected
