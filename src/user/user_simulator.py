"""
User simulator module for simulating user responses.

This module provides functionality to simulate user responses during the information
collection process, for testing or demonstration purposes.
"""

import os
from typing import Any, Dict, Optional

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src import settings
from src.messenger.cli import CLIMessenger


class UserSimulator:
    """
    Simulates a user using an LLM.

    This class handles responding to questions from the user manager as if it were a real user,
    generating realistic responses based on the conversation context.

    Attributes:
        user_id: Unique identifier for the user and conversation to monitor
        messenger: Instance of CLIMessenger for communication
        llm: LLM client for natural language processing
        simulation_profile: Optional dictionary containing predefined user responses and preferences
    """

    def __init__(
        self, user_id: str, simulation_profile: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the UserSimulator.

        Args:
            user_id: The ID of the user and conversation to monitor
            simulation_profile: Optional dictionary containing predefined user details for simulation
        """
        self.user_id = user_id
        self.messenger = CLIMessenger(self.user_id)
        self.simulation_profile = simulation_profile or {}

        # Initialize the LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        model_name = settings.get("OPENAI_MODEL", None)
        if model_name is None:
            raise ValueError("OPENAI_MODEL environment variable is not set")

        # Using a higher temperature for more varied user responses
        self.llm = ChatOpenAI(model=model_name, temperature=0.8)

    def process_and_respond(self) -> None:
        """
        Process the latest message in the conversation and generate a response.

        This method checks the conversation history, and if there's a new message
        from the assistant that hasn't been replied to yet, it generates a
        user-like response and adds it to the conversation.
        """
        # Get the conversation history
        conversation_history = self.messenger.get_conversation_history()

        # If the last message is from the assistant (i.e., the user manager),
        # then we need to respond to it
        if conversation_history and conversation_history[-1]["sender"] == "assistant":
            # Create a system message for the user persona
            profile_str = self._format_simulation_profile()

            system_content = (
                "You are simulating a traveler who is planning a trip and answering"
                " questions from a travel assistant. Respond naturally as if you were"
                " the traveler. Keep answers relatively brief and conversational, as a"
                " real person would type. Include occasional typos, use of casual"
                " language, or slight hesitations to make responses more realistic. If"
                " any information is asked just make up a plausable answer. You never"
                " have to consult anyone and always have an answer ready."
            )

            if profile_str:
                system_content += (
                    f"\n\nUse this profile for your responses:\n{profile_str}"
                )

            system_message = SystemMessage(content=system_content)

            # Get conversation history as langchain messages
            messages = [system_message]
            messages.extend(
                self.messenger.get_conversation_history(as_langchain_messages=True)
            )

            # Generate response
            response = self.llm.invoke(messages)

            # Send the response as coming from the user, not the assistant
            self.messenger.send(response.content, sender="user")

    def _format_simulation_profile(self) -> str:
        """
        Format the simulation profile into a string for the LLM.

        Returns:
            str: Formatted string describing the simulation profile
        """
        if not self.simulation_profile:
            return ""

        profile_parts = []
        for key, value in self.simulation_profile.items():
            if isinstance(value, (list, dict)):
                formatted_value = str(value)
            else:
                formatted_value = value

            profile_parts.append(f"- {key}: {formatted_value}")

        return "\n".join(profile_parts)

    def set_simulation_profile(self, profile: Dict[str, Any]) -> None:
        """
        Set or update the simulation profile.

        Args:
            profile: Dictionary containing predefined user details for simulation
        """
        self.simulation_profile = profile
