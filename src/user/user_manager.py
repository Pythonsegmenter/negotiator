"""
User management module for handling user information collection and storage.

This module provides functionality to manage user data, including collecting,
validating, and persisting user information.
"""

import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src import settings
from src.data_manager import generate_id, load_user_info, save_user_info
from src.messenger.cli import CLIMessenger
from src.user.user_simulator import UserSimulator


@dataclass
class UserInfo:
    """
    Data class representing user information.

    Attributes:
        id: Unique identifier for the user
        activity: The activity the user wants to do (e.g. "Climb Mt Agung at sunrise")
        location: Where the activity takes place (e.g. "Mount Agung, Bali")
        start_time: When the activity starts, in ISO format with timezone
        deadline_negotation: Deadline for completing negotiations, in ISO format with timezone
        participants: Number of people participating in the activity
        budget: Maximum budget for the activity
        guide_contact_details: Dictionary of guide names and their contact information
        preferences: Dictionary containing user preferences like price_vs_value
        additional_info: Dictionary containing additional information about the user for example {names_of_people_traveling: ["John Doe", "Jane Smith"]}
        user_confirmed_correctness: Boolean flag to indicate if the user has confirmed that all information is correct
    """

    id: str
    activity: Optional[str] = None
    location: Optional[str] = None
    start_time: Optional[str] = None
    deadline_negotation: Optional[str] = None
    participants: Optional[int] = None
    budget: Optional[float] = None
    guide_contact_details: Dict[str, str] = field(default_factory=dict)
    preferences: Dict[str, Any] = field(default_factory=dict)
    additional_info: Dict[str, Any] = field(default_factory=dict)
    user_confirmed_correctness: Optional[bool] = None


class UserManager:
    """
    Manages user information collection, validation, and storage.

    This class provides methods to collect and validate user information,
    update user preferences, and handle user data persistence.

    Attributes:
        user_id: Unique identifier for the user and the conversation
        messenger: Instance of CLIMessenger for communication
        user_info: UserInfo object containing the user information
        llm: LLM client for natural language processing
        structured_llm: LLM client configured for structured output
        simulation: Whether to simulate user responses with an LLM
        user_simulator: Optional UserSimulator for simulated users
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        simulation: bool = False,
        simulation_profile: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the UserManager.

        Sets up the messenger, user info object, and conversation history.
        Initializes the OpenAI LLM client.

        Args:
            user_id: Optional ID for the user. If None, a new ID will be generated.
            simulation: Whether to simulate user responses with an LLM
            simulation_profile: Optional dictionary containing predefined user details for simulation
        """
        # Generate a new ID if one isn't provided
        self.user_id = user_id if user_id else generate_id()
        self.simulation = simulation

        # Initialize the messenger with the user ID (used as conversation ID)
        self.messenger = CLIMessenger(self.user_id, create_new=True)

        # Try to load existing user info, or create a new one
        loaded_info = load_user_info(self.user_id)
        if loaded_info:
            # Convert the loaded dictionary to a UserInfo object
            self.user_info = UserInfo(**loaded_info)
        else:
            # Create a new UserInfo with the generated ID
            self.user_info = UserInfo(id=self.user_id)

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
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the user",
                },
                "activity": {
                    "type": "string",
                    "description": (
                        "The activity the user wants to do (e.g. 'Climb Mt Agung at"
                        " sunrise')"
                    ),
                },
                "location": {
                    "type": "string",
                    "description": (
                        "Where the activity takes place (e.g. 'Mount Agung, Bali')"
                    ),
                },
                "start_time": {
                    "type": "string",
                    "description": (
                        "When the activity starts, in ISO format with timezone if"
                        " possible"
                    ),
                },
                "deadline_negotation": {
                    "type": "string",
                    "description": (
                        "Deadline for completing negotiations, in ISO format with"
                        " timezone if possible"
                    ),
                },
                "participants": {
                    "type": "integer",
                    "description": "Number of people participating in the activity",
                },
                "budget": {
                    "type": "number",
                    "description": "Maximum budget for the activity",
                },
                "guide_contact_details": {
                    "type": "object",
                    "description": (
                        "Dictionary of guide names and their contact information. This"
                        " is to be provided by the user. The assistant should not"
                        " suggest guides. (e.g. {'John Doe': '012346548'})"
                    ),
                },
                "preferences": {
                    "type": "object",
                    "description": (
                        "Dictionary containing user preferences like price_vs_value"
                    ),
                },
                "additional_info": {
                    "type": "object",
                    "description": (
                        "Dictionary containing additional information about the user"
                        " for example {names_of_people_traveling: ['John Doe', 'Jane"
                        " Smith']}"
                    ),
                },
                "user_confirmed_correctness": {
                    "type": "boolean",
                    "description": (
                        "Whether the user has confirmed that all information is correct"
                    ),
                },
            },
        }

        # Create a structured output LLM
        self.structured_llm = self.llm.with_structured_output(self.user_info_schema)

        # Create a user simulator if needed
        self.user_simulator = (
            UserSimulator(self.user_id, simulation_profile) if simulation else None
        )

    def collect_user_info(self, questions: List[str] = []) -> None:
        """
        Collect user information from the user through an interactive conversation.

        This method handles the conversation flow, extracts information from user messages,
        and prompts for missing information until all required data is collected and confirmed.
        """

        if not questions:
            # Send an initial message to the user and start the conversation
            self.messenger.send(
                "Hello, I'm Trippy. I'll help you negotiate the best deal for your"
                " trip. What do you want to do?"
            )
        else:
            # Join all questions together in one message
            combined_questions = "\n".join([f"- {question}" for question in questions])
            self.messenger.send(
                "The guides had the following questions about your"
                f" trip:\n{combined_questions}\n\nPlease provide answers to help us"
                " negotiate the best deal for you."
            )
        # If simulation is enabled, get the user simulator to respond
        if self.simulation and self.user_simulator:
            self.user_simulator.process_and_respond()
        else:
            # Get initial input from the user
            self.messenger.receive()

        # Process the initial information
        self._process_user_information()

        # Continue the conversation until we have all required information
        while not self._is_user_info_complete():
            # Generate a follow-up question based on missing information
            follow_up_question = self._generate_follow_up_question()
            self.messenger.send(follow_up_question)

            # If simulation is enabled, get the user simulator to respond
            if self.simulation and self.user_simulator:
                self.user_simulator.process_and_respond()
            else:
                # Get user's response to the follow-up
                self.messenger.receive()

            # Process the new information
            self._process_user_information()

        # Check if the user provided an answer to all questions
        if questions:
            questions_status = self._verify_questions_answered(questions)
            missing_answers: List[str] = questions_status.get("missing_answers", [])

            # If there are still unanswered questions, ask them explicitly
            while missing_answers:
                # Format the missing questions
                missing_questions_text = "\n".join([f"- {q}" for q in missing_answers])
                self.messenger.send(
                    "I still need some information to negotiate the best deal for you."
                    f" Please answer these questions:\n{missing_questions_text}"
                )

                # Get the user's response
                if self.simulation and self.user_simulator:
                    self.user_simulator.process_and_respond()
                else:
                    self.messenger.receive()

                # Process the new information
                self._process_user_information()

                # Check again if all questions are answered
                questions_status = self._verify_questions_answered(questions)
                missing_answers = questions_status.get("missing_answers", [])

        # Continue until the user confirms the information is correct
        while not self.user_info.user_confirmed_correctness:
            # Generate summary of collected information
            summary = self._generate_information_summary()
            confirmation_prompt = (
                f"{summary}\n\nIs all of this information correct? Please review it"
                " carefully.\nIf everything looks good, please confirm. If anything"
                " needs to be changed, please let me know what needs to be corrected."
            )
            self.messenger.send(confirmation_prompt)

            # If simulation is enabled, get the user simulator to respond
            if self.simulation and self.user_simulator:
                self.user_simulator.process_and_respond()
            else:
                # Get user's confirmation or correction
                self.messenger.receive()

            # Process the response to check for confirmation or updates
            self._process_user_confirmation(self.messenger.get_last_message_content())

        # Send final confirmation message
        self.messenger.send("Thank you, we've got all we need. We'll get to work!")

    def _process_user_information(self) -> None:
        """
        Process the conversation history to extract user information.

        Uses the LLM to analyze the conversation and update the user_info object.
        """
        try:
            # Create the system message
            system_message = SystemMessage(
                content=(
                    "You are an assistant that extracts travel information from"
                    " conversations."
                )
            )

            current_info = asdict(self.user_info)

            # Create the human message with task instructions
            prompt_content = f"""
            # Current User Information
            ```
            {current_info}
            ```

            # Task
            Analyze the conversation history to identify any new information about the user's travel plans.
            Extract or update the following fields based on the conversation:
            - activity: What activity they want to do
            - location: Where the activity takes place
            - start_time: When the activity starts
            - deadline_negotation: Deadline for completing negotiations
            - participants: Number of people participating
            - budget: Maximum budget for the activity
            - guide_contact_details: Name and phone number of the guides with whom to negotiate, the user should provide the contact details. You don't suggest guides. (e.g. 'John Doe': '081234567890')
            - preferences: Any specific preferences like price_vs_value ("lowest_price" or "best_value")
            - additional_info: Any additional information about the user for example -names_of_people_traveling: ["John Doe", "Jane Smith"]-

            Do NOT update the id or user_confirmed_correctness fields, as these will be handled separately.

            If there is no information for a field, don't include it in your response.
            If a value should be numeric (participants, budget), convert it to a number.
            If there is a specific question being asked by the guides, add the answer to it to the additional_info field if an answer is provided.
            """

            # Get the conversation history as langchain messages
            messages = [system_message]
            messages.extend(
                self.messenger.get_conversation_history(as_langchain_messages=True)
            )
            messages.append(HumanMessage(content=prompt_content))

            # Extract and update user information
            extracted_info = self.structured_llm.invoke(messages)

            # Update the user_info object with the extracted information
            for key, value in extracted_info.items():
                if key == "id":
                    # Don't update the ID
                    continue
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
        Save the current user information to the user_info JSON file.
        """
        user_info_dict = asdict(self.user_info)
        save_user_info(user_info_dict)

    def load_saved_user_info(self) -> bool:
        """
        Load user information from the user_info JSON file if it exists.

        Returns:
            bool: True if user information was loaded successfully, False otherwise
        """
        saved_info = load_user_info(self.user_id)
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
            "activity",
            "location",
            "start_time",
            "deadline_negotation",
            "participants",
            "budget",
        ]

        for field_name in required_fields:
            if getattr(self.user_info, field_name) is None:
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
        for field_name in [
            "activity",
            "location",
            "start_time",
            "deadline_negotation",
            "participants",
            "budget",
        ]:
            if getattr(self.user_info, field_name) is None:
                missing_fields.append(field_name)

        # Check if guide_contact_details is empty
        if not self.user_info.guide_contact_details:
            missing_fields.append("guide_contact_details")

        # Create system and human messages for the LLM
        system_message = SystemMessage(
            content="""
        You are a travel assistant helping a user plan their trip.
        You need to ask for missing information in a conversational way.
        """
        )

        # Get the conversation history
        messages = [system_message]
        messages.extend(
            self.messenger.get_conversation_history(as_langchain_messages=True)
        )

        human_content = f"""
        # Missing information we need:
        {', '.join(missing_fields)}

        # Task:
        Generate a single, natural-sounding follow-up question to ask the user for the missing information.
        Be conversational and friendly, and try to ask for the information in context of what they've already told you.
        Only ask for 1-2 pieces of missing information at a time, not everything at once.
        Don't explicitly mention we're filling out a form or collecting specific fields.

        Do NOT suggest to find guides for the user. The user should provide the contact details.
        """

        messages.append(HumanMessage(content=human_content))

        # Use LLM to generate the follow-up question
        result = self.llm.invoke(messages)
        return result.content

    def _generate_information_summary(self) -> str:
        """
        Generate a human-readable summary of all collected user information.

        Returns:
            str: A formatted summary of the collected user information
        """
        user_info_dict = asdict(self.user_info)
        # Remove the confirmation field and ID from the summary
        if "user_confirmed_correctness" in user_info_dict:
            del user_info_dict["user_confirmed_correctness"]
        if "id" in user_info_dict:
            del user_info_dict["id"]

        # Format preferences nicely if they exist
        preferences_str = ""
        if user_info_dict.get("preferences"):
            preferences = user_info_dict.pop("preferences")
            preferences_str = "\n".join(
                [
                    f"  • {k.replace('_', ' ').title()}: {v}"
                    for k, v in preferences.items()
                ]
            )
            if preferences_str:
                preferences_str = f"\n\nPreferences:\n{preferences_str}"

        # Format guide contact details
        guide_contacts_str = ""
        if user_info_dict.get("guide_contact_details"):
            guide_contacts = user_info_dict.pop("guide_contact_details")
            guide_contacts_str = "\n".join(
                [f"  • {name}: {contact}" for name, contact in guide_contacts.items()]
            )
            if guide_contacts_str:
                guide_contacts_str = f"\n\nGuide Contacts:\n{guide_contacts_str}"

        # Format additional information if it exists
        additional_info_str = ""
        if user_info_dict.get("additional_info"):
            additional_info = user_info_dict.pop("additional_info")
            additional_info_items = []
            for key, value in additional_info.items():
                if isinstance(value, (list, dict)):
                    formatted_value = str(value)
                else:
                    formatted_value = value
                additional_info_items.append(
                    f"  • {key.replace('_', ' ').title()}: {formatted_value}"
                )

            if additional_info_items:
                additional_info_str = "\n".join(additional_info_items)
                additional_info_str = (
                    f"\n\nAdditional Information:\n{additional_info_str}"
                )

        # Format dates and times for better readability
        start_time = user_info_dict.get("start_time", "Not specified")
        deadline = user_info_dict.get("deadline_negotation", "Not specified")

        # Create a formatted summary
        summary_parts = [
            "📋 Here's a summary of your trip information:",
            f"🎯 Activity: {user_info_dict.get('activity', 'Not specified')}",
            f"📍 Location: {user_info_dict.get('location', 'Not specified')}",
            f"📅 Start Time: {start_time}",
            f"⏱️ Negotiation Deadline: {deadline}",
            (
                "👥 Number of Participants:"
                f" {user_info_dict.get('participants', 'Not specified')}"
            ),
            f"💰 Budget: {user_info_dict.get('budget', 'Not specified')}",
        ]

        summary = "\n".join(summary_parts)
        if guide_contacts_str:
            summary += guide_contacts_str
        if preferences_str:
            summary += preferences_str
        if additional_info_str:
            summary += additional_info_str

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
            system_message = SystemMessage(
                content="""
            You are an assistant analyzing a user's response to a confirmation prompt.
            Your task is to determine if the user has confirmed their information is correct,
            or if they've indicated changes are needed.
            """
            )

            current_info = asdict(self.user_info)

            # Create a task instruction message
            prompt_content = f"""
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
            Do NOT change the "id" field.
            """

            # Get the confirmation messages
            messages = [system_message]
            messages.append(HumanMessage(content=prompt_content))

            # Extract and update user information
            updated_info = self.structured_llm.invoke(messages)

            # Update the user_info object with the extracted information
            for key, value in updated_info.items():
                if key == "id":
                    # Don't update the ID
                    continue
                if key == "preferences" and isinstance(value, dict):
                    self.user_info.preferences.update(value)
                elif value is not None:
                    setattr(self.user_info, key, value)

            # Save the updated user information to the JSON file
            self._save_user_info()

            # If the user provided updates and confirmation is still false, inform them
            if not self.user_info.user_confirmed_correctness:
                self.messenger.send(
                    "I've updated your information. Let me show you the new summary."
                )

        except Exception as e:
            self.messenger.send(f"Error processing user confirmation: {e}")
            self.user_info.user_confirmed_correctness = False

    def _verify_questions_answered(self, questions: List[str]) -> Dict[str, Any]:
        """
        Check if all questions have been answered in the conversation and correctly captured in user_info.

        This method uses the LLM to analyze the conversation history and user information
        to determine if all the questions that were asked have been answered.

        Args:
            questions: List of questions that were asked

        Returns:
            Dict[str, Any]: Dictionary containing questions_status (Dict[str, bool]) and missing_answers (List[str])
        """
        if not questions:
            return {}

        # Create the system message
        system_message = SystemMessage(
            content=(
                "You are an assistant that analyzes conversations to determine if"
                " questions have been answered."
            )
        )

        # Prepare current user info
        current_info = asdict(self.user_info)

        # Define the schema for structured output
        questions_answered_schema = {
            "title": "QuestionsAnsweredStatus",
            "description": (
                "Status of whether questions have been answered in the conversation"
            ),
            "type": "object",
            "properties": {
                "questions_status": {
                    "type": "object",
                    "description": (
                        "A mapping of each question to whether it was properly"
                        " addressed"
                    ),
                    "additionalProperties": {
                        "type": "boolean",
                        "description": (
                            "Whether the question was answered (true) or not (false)"
                        ),
                    },
                },
                "missing_answers": {
                    "type": "array",
                    "description": "List of questions that still need answers",
                    "items": {"type": "string"},
                },
            },
            "required": ["questions_status", "missing_answers"],
        }

        # Create a structured LLM for this specific task
        questions_llm = self.llm.with_structured_output(questions_answered_schema)

        # Get the conversation history
        messages = [system_message]
        messages.extend(
            self.messenger.get_conversation_history(as_langchain_messages=True)
        )

        # Create the human message with task instructions
        prompt_content = f"""
        # Questions That Need Answers
        ```
        {questions}
        ```

        # Current User Information
        ```
        {current_info}
        ```

        # Task
        Analyze the conversation history to determine:
        1. Whether each question in the list has been answered by the user in the conversation
        2. Whether the answer to each question is correctly captured in the user_info

        For each question, return:
        - true if the question was answered and the information is correctly captured
        - false if the question was not answered or the information is not correctly captured

        Also, provide a list of questions that still need answers.
        """

        # Add the prompt content as a human message
        messages.append(HumanMessage(content=prompt_content))

        # Get the results
        result = questions_llm.invoke(messages)

        return result
