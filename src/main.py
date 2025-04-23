"""Main entry point for the Negotiator Travel Agent application."""

import datetime
from dataclasses import asdict
from typing import Any, Dict, List

from src import logger, settings
from src.data_manager import (
    clear_data_dir,
    load_all_guide_info,
    load_user_id,
    load_user_info,
)
from src.guide.guide_manager import GuideManager
from src.user.user_manager import UserManager


def all_negotiations_finished(guide_info_list: List[Dict[str, Any]]) -> bool:
    """
    Check if all guide negotiations are finished.

    Args:
        guide_info_list: List of guide info dictionaries

    Returns:
        bool: True if all guides have negotiation_status of "finished", False otherwise
    """
    if not guide_info_list:
        return False

    for guide_info in guide_info_list:
        if guide_info.get("_negotiation_status", "ongoing") != "finished":
            return False

    return True


def is_past_deadline(deadline_negotiation: str | None) -> bool:
    """
    Check if the current time is past the negotiation deadline.

    Args:
        deadline_negotiation: Deadline string in ISO format

    Returns:
        bool: True if current time is past the deadline, False otherwise
    """
    if not deadline_negotiation:
        return False

    try:
        # Parse the deadline string to a datetime object
        deadline = datetime.datetime.fromisoformat(deadline_negotiation)
        current_time = datetime.datetime.now()

        # Check if current time is past the deadline
        return current_time > deadline
    except (ValueError, TypeError):
        # If the deadline string is invalid, return False
        return False


def main() -> None:
    """Initialize and run the main application flow."""

    if not settings.SKIP_USER_DATA_COLLECTION:
        # Clear data directory to start fresh
        clear_data_dir()

        # Initialize the user manager to collect trip requirements
        user_manager = UserManager(
            simulation=settings.SIMULATION,
            simulation_profile=settings.USER_SIMULATION_PROFILE,
        )

        # Collect user information through conversation
        user_manager.collect_user_info()
    else:
        # Load user manager with existing user ID (can be found in file)
        user_manager = UserManager(user_id=load_user_id())

    # Initialize the guide manager with user ID and simulation flag
    user_info = load_user_info(user_manager.user_id)
    guide_managers = []
    for guide_name in user_info.get("guide_contact_details", {}).keys():
        guide_managers.append(
            GuideManager(
                user_id=user_manager.user_id,
                simulation=settings.SIMULATION,
                guide_name=guide_name,
            )
        )

    # Show simulation state to the user
    if settings.SIMULATION:
        logger.info(
            "Running in SIMULATION mode. Guide responses will be generated"
            " automatically."
        )
    else:
        logger.info("Running in REAL mode. Waiting for real guide responses.")

    # Contact a guide with the user's requirements
    for guide_manager in guide_managers:
        guide_manager.contact_guide()

    # Continue the conversation with the guide in a loop until all negotiations
    # are finished or the deadline is reached
    while True:
        # Check if all guides have finished negotiating
        guide_info_list = load_all_guide_info()
        if all_negotiations_finished(guide_info_list):
            logger.info("All guide negotiations have been completed.")
            break

        # Check if we've passed the negotiation deadline
        user_info = asdict(user_manager.user_info)
        deadline = user_info.get("deadline_negotation")
        if deadline and is_past_deadline(deadline):
            logger.info("The negotiation deadline has passed.")
            break

        # Continue the conversation
        questions = []
        for guide_manager in guide_managers:
            question = guide_manager.continue_conversation()
            if question:
                questions.append(question)

        if questions:
            user_manager.collect_user_info(questions)
        questions = []  # reset questions

    logger.info("completed all negotiations")


if __name__ == "__main__":
    main()
