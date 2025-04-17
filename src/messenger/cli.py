"""Command Line Interface for the messenger module."""

from typing import Optional, List, Dict
from src.data_manager import save_conversation, load_conversation

class CLIMessenger:
    """
    A CLI-based messenger for sending and receiving messages.
    
    This class provides a simple interface for CLI-based communication
    and manages the conversation history.
    
    Attributes:
        conversation_id: Unique identifier for the conversation
        conversation_history: List of messages in the conversation
    """
    
    def __init__(self, conversation_id: Optional[str] = None):
        """
        Initialize the CLI messenger.
        
        Args:
            conversation_id: Unique identifier for the conversation
        """
        self.conversation_id = conversation_id
        self.conversation_history: List[Dict[str, str]] = []
        
        # Load conversation history if an ID is provided
        if self.conversation_id:
            self.conversation_history = load_conversation(self.conversation_id)
    
    def send(self, text: str) -> None:
        """
        Send a message to the CLI (prints to stdout) and record it in the conversation history.
        
        Args:
            text: The message text to send/display.
        """
        print(text)
        
        # Add message to conversation history
        self.conversation_history.append({"sender": "assistant", "text": text})
        
        # Save the conversation if we have an ID
        if self.conversation_id:
            save_conversation(self.conversation_id, self.conversation_history)
    
    def receive(self, prompt: str="") -> str:
        """
        Receive input from the user via CLI and record it in the conversation history.
        
        Args:
            prompt: The prompt text to display to the user.
            
        Returns:
            str: The user's input response.
        """
        user_input = input(prompt)
        
        # Add message to conversation history
        self.conversation_history.append({"sender": "user", "text": user_input})
        
        # Save the conversation if we have an ID
        if self.conversation_id:
            save_conversation(self.conversation_id, self.conversation_history)
            
        return user_input
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            List of conversation messages
        """
        return self.conversation_history
    
    def get_formatted_conversation(self) -> str:
        """
        Get the conversation history as a formatted string.
        
        Returns:
            str: Formatted conversation history
        """
        return "\n".join([
            f"{msg['sender']}: {msg['text']}" 
            for msg in self.conversation_history
        ]) 