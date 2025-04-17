"""
User management module for handling user information collection and storage.

This module provides functionality to manage user data, including collecting,
validating, and persisting user information.
"""

from typing import Dict, Any, Optional, List, Union, cast
from dataclasses import dataclass, field, asdict
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.messenger.cli import CLIMessenger
from src import settings
from src.data_manager import save_user_info, load_user_info

@dataclass
class UserInfo:
    """
    Data class representing user information.
    
    Attributes:
        activity: The activity the user wants to do (e.g. "Climb Mt Agung at sunrise")
        location: Where the activity takes place (e.g. "Mount Agung, Bali") 
        start_time: When the activity starts, in ISO format with timezone
        deadline_negotation: Deadline for completing negotiations, in ISO format with timezone
        participants: Number of people participating in the activity
        budget: Maximum budget for the activity
        guide_contact_details: Dictionary of guide names and their contact information
        preferences: Dictionary containing user preferences like price_vs_value
        user_confirmed_correctness: Boolean flag to indicate if the user has confirmed that all information is correct
    """
    activity: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[str] = None
    deadline_negotation: Optional[str] = None
    participants: Optional[int] = None
    budget: Optional[float] = None
    guide_contact_details: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    user_confirmed_correctness: Optional[bool] = None


class UserManager:
    """
    Manages user information collection, validation, and storage.
    
    This class provides methods to collect and validate user information,
    update user preferences, and handle user data persistence.
    """
    
    def __init__(self):
        """
        Initialize the UserManager.
        
        Sets up the messenger, user info object, and conversation history.
        Initializes the OpenAI LLM client.
        """
        self.messenger = CLIMessenger()
        self.user_info = UserInfo()
        self.conversation_history: List[Dict[str, str]] = []
        
        # Initialize the LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        model_name = settings.get("OPENAI_MODEL", None)
        if model_name is None:
            raise ValueError("OPENAI_MODEL environment variable is not set")
        self.llm = ChatOpenAI(model=model_name, temperature=0)
        
        # Schema definition for structured output
        self.user_info_schema = {
            "title": "UserInformation",
            "description": "Information about the user's travel plans",
            "type": "object",
            "properties": {
                "activity": {
                    "type": "string",
                    "description": "The activity the user wants to do (e.g. 'Climb Mt Agung at sunrise')"
                },
                "location": {
                    "type": "string",
                    "description": "Where the activity takes place (e.g. 'Mount Agung, Bali')"
                },
                "start_time": {
                    "type": "string",
                    "description": "When the activity starts, in ISO format with timezone if possible"
                },
                "deadline_negotation": {
                    "type": "string",
                    "description": "Deadline for completing negotiations, in ISO format with timezone if possible"
                },
                "participants": {
                    "type": "integer",
                    "description": "Number of people participating in the activity"
                },
                "budget": {
                    "type": "number",
                    "description": "Maximum budget for the activity"
                },
                "guide_contact_details": {
                    "type": "object",
                    "description": "Dictionary of guide names and their contact information (e.g. {'John Doe': 'john@example.com'})"
                },
                "preferences": {
                    "type": "object",
                    "description": "Dictionary containing user preferences like price_vs_value"
                },
                "user_confirmed_correctness": {
                    "type": "boolean",
                    "description": "Whether the user has confirmed that all information is correct"
                }
            }
        }
        
        # Create a structured output LLM
        self.structured_llm = self.llm.with_structured_output(self.user_info_schema)
        
        # Send an initial message to the user and start the conversation
        self._send_and_record("Hello, I'm Trippy. I'll help you negotiate the best deal for your trip. What do you want to do?")
        self.collect_user_info()
    
    def _send_and_record(self, message: str) -> None:
        """
        Send a message to the user and record it in the conversation history.
        
        Args:
            message: The message to send to the user
        """
        self.messenger.send(message)
        self.conversation_history.append({"sender": "assistant", "text": message})
    
    def _receive_and_record(self, prompt: str = "") -> str:
        """
        Receive a message from the user and record it in the conversation history.
        
        Args:
            prompt: Optional prompt to display to the user
            
        Returns:
            str: The user's response
        """
        user_input = self.messenger.receive(prompt)
        self.conversation_history.append({"sender": "user", "text": user_input})
        return user_input
    
    def collect_user_info(self) -> None:
        """
        Collect user information from the user through an interactive conversation.
        
        This method handles the conversation flow, extracts information from user messages,
        and prompts for missing information until all required data is collected and confirmed.
        """
        # Get initial input from the user
        user_input = self._receive_and_record()
        
        # Process the initial information
        self._process_user_information()
        
        # Continue the conversation until we have all required information
        while not self._is_user_info_complete():
            # Generate a follow-up question based on missing information
            follow_up_question = self._generate_follow_up_question()
            self._send_and_record(follow_up_question)
            
            # Get user's response to the follow-up
            self._receive_and_record()
            
            # Process the new information
            self._process_user_information()
        
        # Continue until the user confirms the information is correct
        while not self.user_info.user_confirmed_correctness:
            # Generate summary of collected information
            summary = self._generate_information_summary()
            confirmation_prompt = (
                f"{summary}\n\n"
                "Is all of this information correct? Please review it carefully.\n"
                "If everything looks good, please confirm. "
                "If anything needs to be changed, please let me know what needs to be corrected."
            )
            self._send_and_record(confirmation_prompt)
            
            # Get user's confirmation or correction
            user_response = self._receive_and_record()
            
            # Process the response to check for confirmation or updates
            self._process_user_confirmation(user_response)
        
        # Send final confirmation message
        self._send_and_record("Thank you, we've got all we need. I'll start negotiating the best deal for your trip.")
    
    def _process_user_information(self) -> None:
        """
        Process the conversation history to extract user information.
        
        Uses the LLM to analyze the conversation and update the user_info object.
        """
        try:
            # Create the system message
            system_message = SystemMessage(content="You are an assistant that extracts travel information from conversations.")
            
            # Create the human message with the conversation context and current state
            formatted_conversation = "\n".join([
                f"{msg['sender']}: {msg['text']}" 
                for msg in self.conversation_history
            ])
            
            current_info = asdict(self.user_info)
            prompt_content = f"""
            # Current User Information
            ```
            {current_info}
            ```
            
            # Conversation History
            {formatted_conversation}
            
            # Task
            Analyze the conversation history to identify any new information about the user's travel plans.
            Extract or update the following fields based on the conversation:
            - activity: What activity they want to do
            - location: Where the activity takes place 
            - start_time: When the activity starts
            - deadline_negotation: Deadline for completing negotiations
            - participants: Number of people participating
            - budget: Maximum budget for the activity
            - guide_contact_details: Name and phone number of the guides with whom to negotiate (e.g. 'John Doe': '081234567890')
            - preferences: Any specific preferences like price_vs_value ("lowest_price" or "best_value")
            
            Do NOT update the user_confirmed_correctness field, as this will be handled separately.
            
            If there is no information for a field, don't include it in your response.
            If a value should be numeric (participants, budget), convert it to a number.
            """
            
            # Extract and update user information
            extracted_info = self.structured_llm.invoke([
                system_message,
                HumanMessage(content=prompt_content)
            ])
            
            # Update the user_info object with the extracted information
            for key, value in extracted_info.items():
                if key == "preferences" and isinstance(value, dict):
                    self.user_info.preferences.update(value)
                elif value is not None:
                    setattr(self.user_info, key, value)
            
            # Save the updated user information to the JSON file
            self._save_user_info()
            
        except Exception as e:
            self.messenger.send(f"Error processing user information: {e}")
    
    def _save_user_info(self) -> None:
        """
        Save the current user information to the user_info.json file.
        """
        user_info_dict = asdict(self.user_info)
        save_user_info(user_info_dict)
    
    def load_saved_user_info(self) -> bool:
        """
        Load user information from the user_info.json file if it exists.
        
        Returns:
            bool: True if user information was loaded successfully, False otherwise
        """
        saved_info = load_user_info()
        if saved_info:
            # Update the user_info object with the loaded information
            for key, value in saved_info.items():
                setattr(self.user_info, key, value)
            return True
        return False
    
    def _is_user_info_complete(self) -> bool:
        """
        Check if all required user information is present.
        
        This method only checks for the core required fields, excluding user_confirmed_correctness
        since that is set through the confirmation process.
        
        Returns:
            bool: True if all required fields have values, False otherwise
        """
        required_fields = [
            "activity", "location", "start_time", 
            "deadline_negotation", "participants", "budget"
        ]
        
        for field in required_fields:
            if getattr(self.user_info, field) is None:
                return False
        
        # Check if guide_contact_details is empty
        if not self.user_info.guide_contact_details:
            return False
        
        return True
    
    def _generate_follow_up_question(self) -> str:
        """
        Generate a follow-up question to ask for missing information.
        
        Uses the LLM to generate a natural-sounding question based on the conversation
        history and the missing information.
        
        Returns:
            str: A follow-up question for the user
        """
        # Find missing fields
        missing_fields = []
        for field in ["activity", "location", "start_time", "deadline_negotation", "participants", "budget"]:
            if getattr(self.user_info, field) is None:
                missing_fields.append(field)
        
        # Check if guide_contact_details is empty
        if not self.user_info.guide_contact_details:
            missing_fields.append("guide_contact_details")
        
        # Create system and human messages for the LLM
        system_message = SystemMessage(content="""
        You are a travel assistant helping a user plan their trip. 
        You need to ask for missing information in a conversational way.
        """)
        
        formatted_conversation = "\n".join([
            f"{msg['sender']}: {msg['text']}" 
            for msg in self.conversation_history
        ])
        
        human_content = f"""
        # Conversation so far:
        {formatted_conversation}
        
        # Missing information we need:
        {', '.join(missing_fields)}
        
        # Task:
        Generate a single, natural-sounding follow-up question to ask the user for the missing information.
        Be conversational and friendly, and try to ask for the information in context of what they've already told you.
        Only ask for 1-2 pieces of missing information at a time, not everything at once.
        Don't explicitly mention we're filling out a form or collecting specific fields.
        """
        
        human_message = HumanMessage(content=human_content)
        
        # Use LLM to generate the follow-up question
        result = self.llm.invoke([system_message, human_message])
        return result.content
    
    def _generate_information_summary(self) -> str:
        """
        Generate a human-readable summary of all collected user information.
        
        Returns:
            str: A formatted summary of the collected user information
        """
        user_info_dict = asdict(self.user_info)
        # Remove the confirmation field from the summary
        if "user_confirmed_correctness" in user_info_dict:
            del user_info_dict["user_confirmed_correctness"]
        
        # Format preferences nicely if they exist
        preferences_str = ""
        if user_info_dict.get("preferences"):
            preferences = user_info_dict.pop("preferences")
            preferences_str = "\n".join([f"  • {k.replace('_', ' ').title()}: {v}" for k, v in preferences.items()])
            if preferences_str:
                preferences_str = f"\n\nPreferences:\n{preferences_str}"
        
        # Format guide contact details
        guide_contacts_str = ""
        if user_info_dict.get("guide_contact_details"):
            guide_contacts = user_info_dict.pop("guide_contact_details")
            guide_contacts_str = "\n".join([f"  • {name}: {contact}" for name, contact in guide_contacts.items()])
            if guide_contacts_str:
                guide_contacts_str = f"\n\nGuide Contacts:\n{guide_contacts_str}"
        
        # Format dates and times for better readability
        start_time = user_info_dict.get('start_time', 'Not specified')
        deadline = user_info_dict.get('deadline_negotation', 'Not specified')
        
        # Create a formatted summary
        summary_parts = [
            "📋 Here's a summary of your trip information:",
            f"🎯 Activity: {user_info_dict.get('activity', 'Not specified')}",
            f"📍 Location: {user_info_dict.get('location', 'Not specified')}",
            f"📅 Start Time: {start_time}",
            f"⏱️ Negotiation Deadline: {deadline}",
            f"👥 Number of Participants: {user_info_dict.get('participants', 'Not specified')}",
            f"💰 Budget: {user_info_dict.get('budget', 'Not specified')}"
        ]
        
        summary = "\n".join(summary_parts)
        if guide_contacts_str:
            summary += guide_contacts_str
        if preferences_str:
            summary += preferences_str
            
        return summary
    
    def _process_user_confirmation(self, user_response: str) -> None:
        """
        Process the user's response to the information confirmation prompt.
        
        This method uses the LLM to analyze the user's response to determine if they have
        confirmed the information is correct or if they've indicated changes are needed.
        If changes are needed, it extracts and updates the user information accordingly.
        
        Args:
            user_response: The user's response to the confirmation prompt
        """
        try:
            # Create the system message
            system_message = SystemMessage(content="""
            You are an assistant analyzing a user's response to a confirmation prompt.
            Your task is to determine if the user has confirmed their information is correct,
            or if they've indicated changes are needed.
            """)
            
            # Create the human message with the conversation context and current state
            current_info = asdict(self.user_info)
            
            # Create a simple prompt with the user response and current info
            human_content = f"""
            # Current User Information
            ```
            {current_info}
            ```
            
            # User's Response to Confirmation Prompt
            ```
            {user_response}
            ```
            
            # Task
            1. Analyze the user's response to determine if they have confirmed the information is correct or if changes are needed.
            2. If they've confirmed all information is correct, set "user_confirmed_correctness" to true.
            3. If they've indicated changes are needed, extract the updated information and maintain "user_confirmed_correctness" as false.
            4. If their response is ambiguous or unclear, keep "user_confirmed_correctness" as false.
            
            Return the complete user information object, including any changes the user mentioned.
            Make sure to update any fields that the user has corrected based on their response.
            """
            
            # Extract and update user information
            updated_info = self.structured_llm.invoke([
                system_message,
                HumanMessage(content=human_content)
            ])
            
            # Update the user_info object with the extracted information
            for key, value in updated_info.items():
                if key == "preferences" and isinstance(value, dict):
                    self.user_info.preferences.update(value)
                elif value is not None:
                    setattr(self.user_info, key, value)
            
            # Save the updated user information to the JSON file
            self._save_user_info()
            
            # If the user provided updates and confirmation is still false, inform them
            if not self.user_info.user_confirmed_correctness:
                self._send_and_record("I've updated your information. Let me show you the new summary.")
                
        except Exception as e:
            self.messenger.send(f"Error processing user confirmation: {e}")
            self.user_info.user_confirmed_correctness = False

