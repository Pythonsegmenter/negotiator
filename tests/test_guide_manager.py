"""Tests for the GuideManager class."""

import os
from dataclasses import asdict
from unittest.mock import MagicMock, patch

import pytest

from src.guide.guide_manager import GuideManager


@pytest.fixture
def mock_llm():
    """Create a mock LLM for testing."""
    with patch("src.guide.guide_manager.ChatOpenAI") as mock_chat_openai:
        mock_instance = MagicMock()
        # Create a mock for structured output
        mock_instance.with_structured_output.return_value.invoke.return_value = {
            "price": 100.0,
            "starting_location": "Mount Batur Base Camp",
            "starting_time": "2023-07-15T03:00:00+08:00",
            "trip_description": "Sunrise hike to Mount Batur",
            "paid_extras": {"private transport": 50.0, "packed breakfast": 10.0},
            "free_extras": ["water", "guide", "trekking poles"],
            "_last_message": (
                "I can offer you a Mount Batur sunrise trekking package for $100."
            ),
            "_unanswered_questions": ["Do any participants have medical conditions?"],
        }
        mock_chat_openai.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_guide_messenger():
    """Create a mock CLIMessenger for testing."""
    with patch("src.guide.guide_manager.CLIMessenger") as mock_cli_messenger:
        mock_instance = MagicMock()
        mock_instance.get_conversation_history.return_value = [
            {
                "sender": "assistant",
                "content": (
                    "Hello, I am a travel agent working on behalf of a client. They are"
                    " interested in climbing Mount Batur at sunrise."
                ),
            },
            {
                "sender": "user",
                "content": (
                    "I can offer you a Mount Batur sunrise trekking package for $100."
                    " We'll start at Mount Batur Base Camp at 3:00 AM to reach the"
                    " summit for sunrise. The package includes water, guide, and"
                    " trekking poles. For an additional fee, I can arrange private"
                    " transport ($50) and a packed breakfast ($10). Do any participants"
                    " have medical conditions I should be aware of?"
                ),
            },
        ]
        # For get_last_message_content
        mock_instance.get_last_message_content.return_value = (
            "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
            " start at Mount Batur Base Camp at 3:00 AM to reach the summit for"
            " sunrise. The package includes water, guide, and trekking poles. For an"
            " additional fee, I can arrange private transport ($50) and a packed"
            " breakfast ($10). Do any participants have medical conditions I should be"
            " aware of?"
        )
        mock_cli_messenger.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_save_guide_info():
    """Mock the save_guide_info function."""
    with patch("src.guide.guide_manager.save_guide_info") as mock_save:
        yield mock_save


@pytest.fixture
def mock_load_user_info():
    """Mock the load_user_info function."""
    with patch("src.guide.guide_manager.load_user_info") as mock_load:
        mock_load.return_value = {
            "id": "user-123",
            "activity": "Climb Mount Batur",
            "location": "Mount Batur, Bali",
            "start_time": "2023-07-15T04:00:00+08:00",
            "participants": 4,
            "budget": 500.0,
        }
        yield mock_load


@pytest.fixture
def guide_manager(
    mock_llm, mock_guide_messenger, mock_save_guide_info, mock_load_user_info
):
    """Create a GuideManager instance for testing."""
    # Set up environment variables
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "test_model"

    # Create a GuideManager instance
    user_id = "user-123"
    guide_name = "Bali Hiking Guides"
    manager = GuideManager(user_id=user_id, guide_name=guide_name)

    # Return the manager
    return manager


def test_initialization(guide_manager):
    """Test that the GuideManager initializes correctly."""
    assert guide_manager is not None
    assert guide_manager.user_id == "user-123"
    assert guide_manager.guide_name == "Bali Hiking Guides"
    assert guide_manager.guide_info is not None
    assert guide_manager.guide_info.name == "Bali Hiking Guides"
    assert guide_manager.guide_info.price is None
    assert guide_manager.guide_info._negotiation_status == "ongoing"


def test_process_guide_response(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test processing a guide response updates the guide information correctly."""
    # Process the guide response
    guide_manager._process_guide_response()

    # Check that the guide information was updated correctly
    assert guide_manager.guide_info.price == 100.0
    assert guide_manager.guide_info.starting_location == "Mount Batur Base Camp"
    assert guide_manager.guide_info.starting_time == "2023-07-15T03:00:00+08:00"
    assert guide_manager.guide_info.trip_description == "Sunrise hike to Mount Batur"
    assert guide_manager.guide_info.paid_extras == {
        "private transport": 50.0,
        "packed breakfast": 10.0,
    }
    assert guide_manager.guide_info.free_extras == ["water", "guide", "trekking poles"]
    assert (
        guide_manager.guide_info._last_message
        == "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
        " start at Mount Batur Base Camp at 3:00 AM to reach the summit for sunrise."
        " The package includes water, guide, and trekking poles. For an additional"
        " fee, I can arrange private transport ($50) and a packed breakfast ($10)."
        " Do any participants have medical conditions I should be aware of?"
    )
    assert guide_manager.guide_info._unanswered_questions == [
        "Do any participants have medical conditions?"
    ]

    # Check that the guide information was saved
    mock_save_guide_info.assert_called_once()
    # Verify that the correct guide_info was passed to save_guide_info
    saved_info = mock_save_guide_info.call_args[0][0]
    assert saved_info["price"] == 100.0
    assert saved_info["paid_extras"] == {
        "private transport": 50.0,
        "packed breakfast": 10.0,
    }


def test_process_guide_response_no_new_messages(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test that processing is skipped when there are no new messages from the guide."""
    # First process to set the last message
    guide_manager._process_guide_response()
    mock_save_guide_info.reset_mock()  # Reset the call count

    # Process again with the same message
    guide_manager._process_guide_response()

    # Check that no processing occurred
    mock_save_guide_info.assert_not_called()


def test_process_guide_response_with_empty_response(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test processing a guide response with empty or missing fields."""
    # Change the mock to return partial data
    structed_llm_output = {
        "price": 100.0,
        # No starting_location
        # No starting_time
        "trip_description": "Sunrise hike to Mount Batur",
        # Empty paid_extras
        "paid_extras": {},
        # Empty free_extras
        "free_extras": [],
        "_last_message": (
            "I can offer you a Mount Batur sunrise trekking package for $100."
        ),
        "_unanswered_questions": [],
    }
    guide_manager.llm.with_structured_output.return_value.invoke.return_value = (
        structed_llm_output
    )

    # Process the guide response
    guide_manager._process_guide_response()

    # Check that only the provided fields were updated
    assert guide_manager.guide_info.price == 100.0
    assert (
        guide_manager.guide_info.starting_location == "Mount Batur Base Camp"
    )  # From the previous test's mock
    assert (
        guide_manager.guide_info.starting_time == "2023-07-15T03:00:00+08:00"
    )  # From the previous test's mock
    assert guide_manager.guide_info.trip_description == "Sunrise hike to Mount Batur"
    assert guide_manager.guide_info.paid_extras == {
        "private transport": 50.0,
        "packed breakfast": 10.0,
    }  # From the previous test's mock
    assert guide_manager.guide_info.free_extras == [
        "water",
        "guide",
        "trekking poles",
    ]  # From the previous test's mock
    assert (
        guide_manager.guide_info._last_message
        == "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
        " start at Mount Batur Base Camp at 3:00 AM to reach the summit for sunrise."
        " The package includes water, guide, and trekking poles. For an additional"
        " fee, I can arrange private transport ($50) and a packed breakfast ($10)."
        " Do any participants have medical conditions I should be aware of?"
    )
    assert guide_manager.guide_info._unanswered_questions == [
        "Do any participants have medical conditions?"
    ]  # From the previous test's mock

    # Check that the guide information was saved
    mock_save_guide_info.assert_called_once()


def test_process_guide_response_with_new_message(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test processing when there's a new message from the guide."""
    # First process the initial message
    guide_manager._process_guide_response()

    # Reset the mock and change the conversation history to have a new message
    mock_save_guide_info.reset_mock()
    new_conversation = [
        {
            "sender": "assistant",
            "content": (
                "Hello, I am a travel agent working on behalf of a client. They are"
                " interested in climbing Mount Batur at sunrise."
            ),
        },
        {
            "sender": "user",
            "content": (
                "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
                " start at Mount Batur Base Camp at 3:00 AM to reach the summit for"
                " sunrise. The package includes water, guide, and trekking poles. For"
                " an additional fee, I can arrange private transport ($50) and a packed"
                " breakfast ($10). Do any participants have medical conditions I should"
                " be aware of?"
            ),
        },
        {
            "sender": "assistant",
            "content": "Can you provide a discount for a group of 4 people?",
        },
        {
            "sender": "user",
            "content": (
                "For a group of 4, I can offer a 10% discount, making it $90 per"
                " person."
            ),
        },
    ]
    mock_guide_messenger.get_conversation_history.return_value = new_conversation

    # Update the structured LLM response for the new message
    new_llm_output = {
        "price": 90.0,  # Updated price with discount
        "starting_location": "Mount Batur Base Camp",
        "starting_time": "2023-07-15T03:00:00+08:00",
        "trip_description": "Sunrise hike to Mount Batur",
        "paid_extras": {"private transport": 50.0, "packed breakfast": 10.0},
        "free_extras": ["water", "guide", "trekking poles"],
        "_last_message": (
            "For a group of 4, I can offer a 10% discount, making it $90 per person."
        ),
        "_unanswered_questions": [],  # Question was answered
    }
    guide_manager.llm.with_structured_output.return_value.invoke.return_value = (
        new_llm_output
    )

    # Process the guide response with the new message
    guide_manager._process_guide_response()

    # Check that the guide information was updated with the new price
    assert guide_manager.guide_info.price == 90.0
    assert (
        guide_manager.guide_info._last_message
        == "For a group of 4, I can offer a 10% discount, making it $90 per person."
    )
    assert guide_manager.guide_info._unanswered_questions == []

    # Check that the guide information was saved
    mock_save_guide_info.assert_called_once()


def test_process_guide_response_with_error(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test error handling when processing a guide response."""
    # Make the structured_llm.invoke method raise an exception
    guide_manager.llm.with_structured_output.return_value.invoke.side_effect = (
        Exception("Test error")
    )

    # Process the guide response (should not raise an exception)
    guide_manager._process_guide_response()

    # Check that no information was updated
    assert guide_manager.guide_info.price is None
    assert guide_manager.guide_info.starting_location is None
    assert guide_manager.guide_info.paid_extras == {}

    # Check that the guide information was not saved
    mock_save_guide_info.assert_not_called()


def test_contact_guide_updates_info(
    guide_manager, mock_load_user_info, mock_guide_messenger, mock_save_guide_info
):
    """Test that contacting a guide and receiving a response updates the guide information."""
    # Mock the simulation to be True for this test
    guide_manager.simulation = True
    guide_manager.guide_simulator = MagicMock()

    # Call contact_guide
    guide_manager.contact_guide()

    # Check that a message was sent to the guide
    mock_guide_messenger.send.assert_called_once()

    # Check that the guide simulator was called to process and respond
    guide_manager.guide_simulator.process_and_respond.assert_called_once()

    # Add a new message to the conversation history simulating guide response
    mock_guide_messenger.get_conversation_history.return_value = [
        {
            "sender": "assistant",
            "content": (
                "Hello, I am a travel agent working on behalf of a client. They are"
                " interested in climbing Mount Batur at sunrise."
            ),
        },
        {
            "sender": "user",
            "content": (
                "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
                " start at Mount Batur Base Camp at 3:00 AM to reach the summit for"
                " sunrise. The package includes water, guide, and trekking poles. For"
                " an additional fee, I can arrange private transport ($50) and a packed"
                " breakfast ($10). Do any participants have medical conditions I should"
                " be aware of?"
            ),
        },
    ]

    # Manually process the guide response
    guide_manager._process_guide_response()

    # Check that the guide information was processed
    assert guide_manager.guide_info.price == 100.0
    assert guide_manager.guide_info.starting_location == "Mount Batur Base Camp"

    # Check that the guide information was saved
    mock_save_guide_info.assert_called()


def test_continue_conversation_updates_info(
    guide_manager, mock_guide_messenger, mock_save_guide_info
):
    """Test that continuing a conversation with a guide updates the guide information."""
    # Mock the simulation to be True for this test
    guide_manager.simulation = True
    guide_manager.guide_simulator = MagicMock()

    # Mock the conversation history for _process_guide_response at the start
    original_conversation = [
        {
            "sender": "assistant",
            "content": (
                "Hello, I am a travel agent working on behalf of a client. They are"
                " interested in climbing Mount Batur at sunrise."
            ),
        },
        {
            "sender": "user",
            "content": (
                "I can offer you a Mount Batur sunrise trekking package for $100. We'll"
                " start at Mount Batur Base Camp at 3:00 AM to reach the summit for"
                " sunrise. The package includes water, guide, and trekking poles. For"
                " an additional fee, I can arrange private transport ($50) and a packed"
                " breakfast ($10). Do any participants have medical conditions I should"
                " be aware of?"
            ),
        },
    ]
    mock_guide_messenger.get_conversation_history.return_value = original_conversation

    # Process the initial guide response
    guide_manager._process_guide_response()

    # Mock the load_conversation function for continue_conversation
    with patch("src.guide.guide_manager.load_conversation") as mock_load_conversation:
        mock_load_conversation.return_value = original_conversation

        # Setup mock for load_guide_info
        with patch("src.guide.guide_manager.load_guide_info") as mock_load_guide_info:
            # Don't need to change the guide info format since we're using our current object
            guide_info_dict = asdict(guide_manager.guide_info)
            mock_load_guide_info.return_value = guide_info_dict

            # Setup structured_llm to return a decision to talk to the guide
            decision_llm = MagicMock()
            decision_llm.invoke.return_value = {
                "action": "talk_to_guide",
                "reasoning": "Need to negotiate the price",
                "message": "Can you offer a better price for a group of 4?",
            }
            guide_manager.llm.with_structured_output.return_value = decision_llm

            # Reset the mock to track further calls
            mock_save_guide_info.reset_mock()

            # Call continue_conversation
            result = guide_manager.continue_conversation()

            # Check that a message was sent to the guide
            mock_guide_messenger.send.assert_called_once_with(
                "Can you offer a better price for a group of 4?"
            )

            # Check that the guide simulator was called to process and respond
            guide_manager.guide_simulator.process_and_respond.assert_called_once()

            # Now simulate a new response from the guide
            new_conversation = original_conversation + [
                {
                    "sender": "assistant",
                    "content": "Can you offer a better price for a group of 4?",
                },
                {
                    "sender": "user",
                    "content": (
                        "For a group of 4, I can offer a 10% discount, making it $90"
                        " per person."
                    ),
                },
            ]
            mock_guide_messenger.get_conversation_history.return_value = (
                new_conversation
            )

            # Update LLM mock for the new message
            new_llm_output = {
                "price": 90.0,  # Updated price with discount
                "starting_location": "Mount Batur Base Camp",
                "starting_time": "2023-07-15T03:00:00+08:00",
                "trip_description": "Sunrise hike to Mount Batur",
                "paid_extras": {"private transport": 50.0, "packed breakfast": 10.0},
                "free_extras": ["water", "guide", "trekking poles"],
                "_last_message": (
                    "For a group of 4, I can offer a 10% discount, making it $90 per"
                    " person."
                ),
                "_unanswered_questions": [],  # Question was answered
            }
            guide_manager.llm.with_structured_output.return_value.invoke.return_value = (
                new_llm_output
            )

            # Process the new guide response (normally this would be done by the guide simulator)
            guide_manager._process_guide_response()

            # Check that the guide information was updated with the new price
            assert guide_manager.guide_info.price == 90.0
            assert (
                guide_manager.guide_info._last_message
                == "For a group of 4, I can offer a 10% discount, making it $90 per"
                " person."
            )

            # Check that the guide information was saved
            assert mock_save_guide_info.call_count == 1

            # Check that an empty string was returned (pause negotiation)
            assert result == ""
