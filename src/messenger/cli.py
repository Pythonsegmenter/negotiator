"""Command Line Interface for the messenger module."""

from typing import Dict, List, Union

from langchain_core.messages import HumanMessage, SystemMessage

from src import logger
from src.data_manager import load_conversation, save_conversation


class CLIMessenger:
    """
    A CLI-based messenger for sending and receiving messages.

    This class provides a simple interface for CLI-based communication
    and manages the conversation history.

    Attributes:
        conversation_id: Unique identifier for the conversation (equivalent to user_id or guide_id)
    """

    def __init__(self, conversation_id: str, create_new: bool = False):
        """
        Initialize the CLI messenger.

        Args:
            conversation_id: Unique identifier for the conversation (equivalent to user_id or guide_id)
            create_new: When True, creates a new empty conversation
        """
        self.conversation_id = conversation_id

        # Initialize empty conversation if create_new is True
        if create_new:
            save_conversation(self.conversation_id, [])

    def send(self, text: str, sender: str = "assistant") -> None:
        """
        Send a message to the CLI (prints to stdout) and record it in the conversation history.

        Args:
            text: The message text to send/display.
            sender: The sender of the message. Defaults to "assistant".
                   Can be "assistant", "user", "guide", etc.
        """
        logger.info(f"{sender}: {text}")

        # Get the latest conversation history
        conversation_history = load_conversation(self.conversation_id)

        # Add message to conversation history
        conversation_history.append({"sender": sender, "text": text})

        # Save the conversation
        save_conversation(self.conversation_id, conversation_history)

    def receive(self, prompt: str = "") -> str:
        """
        Receive input from the user via CLI and record it in the conversation history.

        Args:
            prompt: The prompt text to display to the user.

        Returns:
            str: The user's input response.
        """
        user_input = input(prompt)

        # Get the latest conversation history
        conversation_history = load_conversation(self.conversation_id)

        # Add message to conversation history
        conversation_history.append({"sender": "user", "text": user_input})

        # Save the conversation
        save_conversation(self.conversation_id, conversation_history)

        return user_input

    def get_conversation_history(
        self, as_langchain_messages: bool = False
    ) -> Union[List[Dict[str, str]], List[Union[HumanMessage, SystemMessage]]]:
        """
        Get the current conversation history.

        Args:
            as_langchain_messages: When True, returns conversation history as a list
                of langchain HumanMessage and SystemMessage objects instead of dictionaries.

        Returns:
            List of conversation messages as dictionaries or langchain message objects
        """
        conversation_history = load_conversation(self.conversation_id)

        if not as_langchain_messages:
            return conversation_history

        messages = []
        for i, msg in enumerate(conversation_history):
            if msg["sender"] == "user" or msg["sender"] == "assistant":
                messages.append(HumanMessage(content=msg["text"]))
            elif msg["sender"] == "guide" and i < len(conversation_history) - 1:
                # Include guide messages as system messages for context
                # Skip the last guide message if it exists
                messages.append(
                    SystemMessage(content=f"Previous guide response: {msg['text']}")
                )

        return messages

    def get_formatted_conversation(self) -> str:
        """
        Get the conversation history as a formatted string.

        Returns:
            str: Formatted conversation history
        """
        conversation_history = load_conversation(self.conversation_id)
        return "\n".join(
            [f"{msg['sender']}: {msg['text']}" for msg in conversation_history]
        )

    def get_last_message_content(self) -> str:
        """
        Get the content of the last message in the conversation history.

        Returns:
            str: The text content of the last message
        """
        conversation_history = load_conversation(self.conversation_id)
        if conversation_history:
            return conversation_history[-1]["text"]
        return ""
