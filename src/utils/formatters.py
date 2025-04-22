"""
Utility module for formatting data structures consistently across the application.

This module provides helper functions to format user and guide information
in a standardized way for use in prompts and other contexts.
"""

from typing import Any, Dict, List


def format_user_info(user_info: Dict[str, Any]) -> str:
    """
    Format user information into a readable string representation.

    Args:
        user_info: Dictionary containing user information

    Returns:
        str: Formatted user information string
    """
    if not user_info:
        return "No user information available."

    # Format basic fields
    formatted_parts = []

    # Add basic fields with fallbacks
    formatted_parts.append(f"Activity: {user_info.get('activity', 'Not specified')}")
    formatted_parts.append(f"Location: {user_info.get('location', 'Not specified')}")
    formatted_parts.append(
        f"Start Time: {user_info.get('start_time', 'Not specified')}"
    )
    formatted_parts.append(
        f"Participants: {user_info.get('participants', 'Not specified')}"
    )
    formatted_parts.append(f"Budget: {user_info.get('budget', 'Not specified')}")
    formatted_parts.append(
        f"Negotiation Deadline: {user_info.get('deadline_negotation', 'Not specified')}"
    )

    # Format preferences
    if preferences := user_info.get("preferences"):
        pref_items = []
        for key, value in preferences.items():
            pref_items.append(f"  - {key.replace('_', ' ').title()}: {value}")

        if pref_items:
            formatted_parts.append("Preferences:")
            formatted_parts.extend(pref_items)

    # Format guide contacts
    if guide_contacts := user_info.get("guide_contact_details"):
        contact_items = []
        for name, contact in guide_contacts.items():
            contact_items.append(f"  - {name}: {contact}")

        if contact_items:
            formatted_parts.append("Guide Contacts:")
            formatted_parts.extend(contact_items)

    # Format additional info
    if additional_info := user_info.get("additional_info"):
        additional_items = []
        for key, value in additional_info.items():
            if isinstance(value, (list, dict)):
                formatted_value = str(value)
            else:
                formatted_value = value
            additional_items.append(
                f"  - {key.replace('_', ' ').title()}: {formatted_value}"
            )

        if additional_items:
            formatted_parts.append("Additional Information:")
            formatted_parts.extend(additional_items)

    return "\n".join(formatted_parts)


def format_guide_info(guide_info: Dict[str, Any]) -> str:
    """
    Format guide information into a readable string representation.

    Args:
        guide_info: Dictionary containing guide information

    Returns:
        str: Formatted guide information string
    """
    if not guide_info:
        return "No guide information available."

    # Format basic fields
    formatted_parts = []

    # Add basic fields with fallbacks
    formatted_parts.append(f"Name: {guide_info.get('name', 'Not specified')}")
    formatted_parts.append(f"Price: {guide_info.get('price', 'Not specified')}")
    formatted_parts.append(
        f"Starting Location: {guide_info.get('starting_location', 'Not specified')}"
    )
    formatted_parts.append(
        f"Starting Time: {guide_info.get('starting_time', 'Not specified')}"
    )
    formatted_parts.append(
        f"Trip Description: {guide_info.get('trip_description', 'Not specified')}"
    )

    # Format paid extras
    if paid_extras := guide_info.get("paid_extras"):
        extras_items = []
        for service, price in paid_extras.items():
            extras_items.append(f"  - {service}: {price}")

        if extras_items:
            formatted_parts.append("Paid Extras:")
            formatted_parts.extend(extras_items)

    # Format free extras
    if free_extras := guide_info.get("free_extras"):
        if free_extras:
            formatted_parts.append("Free Extras:")
            for extra in free_extras:
                formatted_parts.append(f"  - {extra}")

    # Add negotiation status
    formatted_parts.append(
        f"Negotiation Status: {guide_info.get('_negotiation_status', 'ongoing')}"
    )

    # Add unanswered questions
    if unanswered := guide_info.get("_unanswered_questions"):
        if unanswered:
            formatted_parts.append("Unanswered Questions:")
            for question in unanswered:
                formatted_parts.append(f"  - {question}")

    return "\n".join(formatted_parts)


def format_conversation_history(conversation_history: List[Dict[str, Any]]) -> str:
    """
    Format conversation history into a readable string representation.

    Args:
        conversation_history: List of conversation message dictionaries

    Returns:
        str: Formatted conversation history string
    """
    if not conversation_history:
        return "No conversation history available."

    formatted_messages = []
    for message in conversation_history:
        sender = message.get("sender", "Unknown")
        text = message.get("text", "")
        formatted_messages.append(f"{sender}: {text}")

    return "\n".join(formatted_messages)
