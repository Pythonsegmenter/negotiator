"""
Tests for the complete user flow with actual LLM interactions.

This test module tests the full user flow from entering information to confirming,
changing information, and re-confirming. It verifies that:

1. The application can run from start to finish with user interaction
2. The LLM properly understands and extracts user information
3. Users can reject confirmation to make changes to their data
4. The final user info JSON file accurately reflects all provided information

This test uses real LLM calls rather than mocks to ensure the complete system
works as expected in production scenarios.
"""

import datetime
import os
from unittest.mock import patch

import pytest

from src.data_manager import USER_DIR, load_user_info


@pytest.fixture
def date_data():
    """
    Fixture providing date information for tests.

    Returns:
        dict: Dictionary containing today, tomorrow, and day after tomorrow dates
             both as datetime objects and formatted strings
    """
    today = datetime.datetime.now()
    tomorrow = today + datetime.timedelta(days=1)
    day_after_tomorrow = today + datetime.timedelta(days=2)

    return {
        "today": today,
        "tomorrow": tomorrow,
        "day_after_tomorrow": day_after_tomorrow,
        "today_str": today.strftime("%Y-%m-%d"),
        "tomorrow_str": tomorrow.strftime("%Y-%m-%d"),
        "day_after_tomorrow_str": day_after_tomorrow.strftime("%Y-%m-%d"),
    }


def verify_user_info(expected_values, date_info=None):
    """
    Verify that the saved user info matches expected values.

    This function validates that a user info file exists and that its
    contents match the expected values. It performs case-insensitive comparison
    for text fields and handles date references from the date_info dictionary.

    Args:
        expected_values: Dictionary of expected values to check
        date_info: Optional dictionary containing date strings for verification

    Raises:
        AssertionError: If user info doesn't match expected values or file doesn't exist
    """
    # Check if any user files exist
    assert USER_DIR.exists(), "User directory doesn't exist"

    user_files = list(USER_DIR.glob("*.json"))
    assert len(user_files) > 0, "No user info files were created"

    # Load the first user file found
    user_info = load_user_info()
    assert user_info is not None, "Failed to load user info"

    # Verify user ID exists
    assert "id" in user_info, "User info doesn't contain an ID"

    # Check activity and location (case-insensitive)
    if "activity" in expected_values:
        assert user_info["activity"].lower() == expected_values["activity"].lower(), (
            f"Activity doesn't match expected value: '{user_info['activity']}' vs"
            f" '{expected_values['activity']}'"
        )

    if "location" in expected_values:
        assert user_info["location"].lower() == expected_values["location"].lower(), (
            f"Location doesn't match expected value: '{user_info['location']}' vs"
            f" '{expected_values['location']}'"
        )

    # Check date-related fields
    if "start_time" in expected_values:
        date_str = date_info.get(
            expected_values["start_time"], expected_values["start_time"]
        )
        assert (
            date_str in user_info["start_time"]
        ), f"Start time doesn't include expected date: '{user_info['start_time']}'"

    if "deadline_negotation" in expected_values:
        date_str = date_info.get(
            expected_values["deadline_negotation"],
            expected_values["deadline_negotation"],
        )
        assert date_str in user_info["deadline_negotation"], (
            "Deadline doesn't include expected date:"
            f" '{user_info['deadline_negotation']}'"
        )

    # Check numeric fields
    if "participants" in expected_values:
        assert (
            user_info["participants"] == expected_values["participants"]
        ), f"Participants doesn't match expected value: '{user_info['participants']}'"

    if "budget" in expected_values:
        assert (
            user_info["budget"] == expected_values["budget"]
        ), f"Budget doesn't match expected value: '{user_info['budget']}'"

    # Check guide contact details
    if "guide_contact_details" in expected_values:
        for name, contact in expected_values["guide_contact_details"].items():
            assert name in user_info["guide_contact_details"], (
                f"{name} is missing from guide contacts:"
                f" {user_info['guide_contact_details']}"
            )
            assert user_info["guide_contact_details"][name] == contact, (
                f"{name}'s contact info is incorrect:"
                f" '{user_info['guide_contact_details'][name]}'"
            )

    # Check confirmation status
    if "user_confirmed_correctness" in expected_values:
        assert (
            user_info["user_confirmed_correctness"]
            == expected_values["user_confirmed_correctness"]
        ), (
            "User confirmation status doesn't match:"
            f" {user_info['user_confirmed_correctness']}"
        )


def test_user_flow_with_date_change(date_data):
    """
    Test the complete user flow with date change after initial confirmation.

    This test simulates a user:
    1. Providing initial activity information (climbing Mount Fiji)
    2. Answering follow-up questions about deadline, participants, budget, and guides
    3. Reviewing the information summary and rejecting it
    4. Changing the start date to a day later
    5. Confirming the updated information

    The test verifies that:
    - The user info JSON file is correctly created
    - All information is properly extracted and saved
    - The start date is updated as requested
    - The user confirmation status is set to True after final confirmation

    Args:
        date_data: Fixture providing date information for test scenarios
    """
    # Skip test if OPENAI_API_KEY is not set
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY environment variable is not set")

    # Define the user inputs in sequence with more responses to accommodate the longer conversation
    user_inputs = [
        # Initial activity information
        f"I want to climb mount fiji on {date_data['tomorrow_str']}",
        # Response to follow-up question about participants and budget
        "There will be 1 participant and my budget is 100 dollars",
        # Response to follow-up question about guides
        (
            f"The deadline for negotiation is {date_data['today_str']}. Contact Johnny"
            " at 0123456 and Paula at 012789"
        ),
        # Response to any additional questions about location or details
        "I'll start from Mount Fiji",
        # Response to any additional questions
        "I have all the equipment I need",
        # Response to any additional questions
        "I plan to stay in a hotel near the mountain",
        # Response to the confirmation request
        f"No, I want to change the start date to {date_data['day_after_tomorrow_str']}",
        # Response to any follow-up after change
        "Yes, everything else is correct",
        # Final confirmation
        "Yes, that's all correct now",
        # Extra responses in case they're needed
        "Yes, confirmed",
        "Correct",
        "Yes",
    ]

    # Run the main script with simulated user input
    with patch("builtins.input", side_effect=user_inputs):
        try:
            # Import and run main to trigger the user flow
            from src.main import main

            main()
        except Exception as e:
            pytest.fail(f"Error running main: {e}")

    # Define expected values
    expected_values = {
        "activity": "climb mount fiji",
        "location": "mount fiji",
        "start_time": "day_after_tomorrow_str",  # This will be looked up in date_data
        "deadline_negotation": "today_str",  # This will be looked up in date_data
        "participants": 1,
        "budget": 100,
        "guide_contact_details": {"Johnny": "0123456", "Paula": "012789"},
        "user_confirmed_correctness": True,
    }

    # Verify the user info
    verify_user_info(expected_values, date_data)
