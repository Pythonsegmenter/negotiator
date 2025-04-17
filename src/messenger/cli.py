"""Command Line Interface for the messenger module."""




class CLIMessenger:
    """
    A CLI-based messenger for sending and receiving messages.
    
    This class provides a simple interface for CLI-based communication.
    """
    
    def send(self, text: str) -> None:
        """
        Send a message to the CLI (prints to stdout).
        
        Args:
            text: The message text to send/display.
        """
        print(text)
    
    def receive(self, prompt: str="") -> str:
        """
        Receive input from the user via CLI.
        
        Args:
            prompt: The prompt text to display to the user.
            
        Returns:
            str: The user's input response.
        """
        return input(prompt) 