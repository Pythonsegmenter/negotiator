"""
Guide management module for interacting with travel guides.

This module provides functionality to manage guide interactions, including
creating and managing conversations with guides.
"""

import os
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src import logger, settings
from src.data_manager import (
    generate_id,
    load_conversation,
    load_guide_info,
    load_user_info,
    save_guide_info,
)
from src.guide.guide_simulator import GuideSimulator
from src.messenger.cli import CLIMessenger
from src.utils.formatters import (
    format_conversation_history,
    format_guide_info,
    format_user_info,
)


@dataclass
class GuideInfo:
    """
    Data class representing guide information.

    Attributes:
        id: Unique identifier for the guide
        name: Name of the guide
        price: Price quoted by the guide for the requested service
        starting_location: Starting location for the activity
        starting_time: Starting time for the activity
        trip_description: Description of the trip or activity offered
        paid_extras: Dictionary of extra services offered at an additional cost
        free_extras: List of extra services included at no additional cost
        _last_message: The last message received from the guide
        _unanswered_questions: List of questions from the guide that need answers
        _negotiation_status: Current status of the negotiation (ongoing, completed, etc.)
    """

    id: str
    name: str
    price: Optional[float] = None
    starting_location: Optional[str] = None
    starting_time: Optional[str] = None
    trip_description: str = ""
    paid_extras: Dict[str, float] = field(default_factory=dict)
    free_extras: List[str] = field(default_factory=list)
    _last_message: Optional[str] = None
    _unanswered_questions: List[str] = field(default_factory=list)
    _negotiation_status: str = "ongoing"


class GuideManager:
    """
    Manages interactions with guides, including conversation management.

    This class provides methods to communicate with guides and handle
    negotiation regarding user activities.

    Attributes:
        guide_id: Unique identifier for the guide and conversation
        messenger: Instance of CLIMessenger for communication
        guide_info: GuideInfo object containing the guide information
        llm: LLM client for natural language processing
        simulation: Whether to simulate guide responses with an LLM
        guide_simulator: Optional GuideSimulator for simulated guides
        user_id: Identifier for the user associated with this guide interaction
    """

    def __init__(self, user_id: str, guide_name: str, simulation: bool = False):
        """
        Initialize the GuideManager.

        Sets up the messenger, guide info, and conversation.
        Initializes the OpenAI LLM client.

        Args:
            user_id: ID for the user whose information will be used
            guide_name: Name of the guide to communicate with
            simulation: Whether to simulate guide responses with an LLM
        """
        if not user_id:
            raise ValueError("User ID is required")

        self.guide_id = generate_id()
        self.simulation = simulation
        self.user_id = user_id
        self.guide_name = guide_name
        # Initialize the messenger with the guide_id (as conversation ID)
        self.guide_messenger = CLIMessenger(self.guide_id, create_new=True)

        # Create a new GuideInfo with the guide_id
        self.guide_info = GuideInfo(id=self.guide_id, name=self.guide_name)
        # Save the initial guide info
        self._save_guide_info()

        # Initialize the LLM client for agent's use (not guide simulation)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        model_name = settings.get("OPENAI_MODEL", None)
        if model_name is None:
            raise ValueError("OPENAI_MODEL environment variable is not set")

        self.llm = ChatOpenAI(model=model_name, temperature=0.7)

        # Set up a schema for structured output when processing guide responses
        self.guide_info_schema = {
            "title": "GuideInformation",
            "description": "Information extracted from guide responses",
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Unique identifier for the guide",
                },
                "name": {"type": "string", "description": "Name of the guide"},
                "price": {
                    "type": ["number", "null"],
                    "description": (
                        "Price quoted by the guide for the requested service"
                    ),
                },
                "starting_location": {
                    "type": ["string", "null"],
                    "description": "Starting location for the activity",
                },
                "starting_time": {
                    "type": ["string", "null"],
                    "description": "Starting time for the activity",
                },
                "trip_description": {
                    "type": "string",
                    "description": "Description of the trip or activity offered",
                },
                "paid_extras": {
                    "type": "object",
                    "description": (
                        "Dictionary of extra services offered at an additional cost"
                    ),
                },
                "free_extras": {
                    "type": "array",
                    "description": (
                        "List of extra services included at no additional cost"
                    ),
                    "items": {"type": "string"},
                },
                "_last_message": {
                    "type": ["string", "null"],
                    "description": "The last message received from the guide",
                },
                "_unanswered_questions": {
                    "type": "array",
                    "description": "List of questions from the guide that need answers",
                    "items": {"type": "string"},
                },
                "_negotiation_status": {
                    "type": "string",
                    "description": (
                        "Current status of the negotiation (ongoing, completed, etc.)"
                    ),
                },
            },
        }

        # Create a guide simulator if needed
        self.guide_simulator = GuideSimulator(self.guide_id) if simulation else None

    def _save_guide_info(self) -> None:
        """Save the guide information to a file."""
        guide_info_dict = asdict(self.guide_info)
        save_guide_info(guide_info_dict)

    def _process_guide_response(self) -> None:
        """
        Process the guide's response to update the guide information.

        Analyzes the conversation history to extract and update guide information
        such as pricing, services offered, and other details.

        The method will only process guide information if there's a new message
        in the conversation since the last processing.
        """
        try:
            # Get the most recent message in the conversation
            conversation_history = self.guide_messenger.get_conversation_history()

            # If there's no conversation yet, return
            if not conversation_history:
                return

            # Get the last message
            last_message = conversation_history[-1]

            # Only process if the last message is from the guide (sender = 'user' in the conversation)
            # and it's different from the last processed message
            if (
                last_message.get("sender") != "user"
                or last_message.get("content") == self.guide_info._last_message
            ):
                # No new guide message to process
                return

            # Update the last message field to track what we've processed
            self.guide_info._last_message = last_message.get("content")

            # Create the system message
            system_message = SystemMessage(
                content=(
                    "You are an assistant that extracts information from guide"
                    " responses in travel negotiations. Your job is to identify key"
                    " details such as prices, services, locations, times, and questions"
                    " that need answers."
                )
            )

            # Get the current guide info as a dictionary
            current_info = asdict(self.guide_info)

            # Create the human message with task instructions
            prompt_content = f"""
            # Current Guide Information
            ```
            {current_info}
            ```

            # Task
            Analyze the conversation history to identify any information provided by the guide about:
            - price: The price quoted for the activity
            - starting_location: Where the activity begins
            - starting_time: When the activity starts
            - trip_description: Description of what the activity involves
            - paid_extras: Additional services offered at extra cost (format as dictionary with service: price)
            - free_extras: Additional services included at no extra cost (format as list)
            - _unanswered_questions: Questions the guide has asked that need answers from the traveler

            Do NOT update the id, name, or _negotiation_status fields.
            The _last_message field should contain the guide's most recent message.

            Only include fields in your response if there is relevant information in the conversation.
            If the information is clearly stated in the conversation, update the field.
            If the information is ambiguous or not mentioned, leave the existing value.
            """

            # Get the conversation history as langchain messages
            messages = [system_message]
            messages.extend(
                self.guide_messenger.get_conversation_history(
                    as_langchain_messages=True
                )
            )
            messages.append(HumanMessage(content=prompt_content))

            # Extract guide information from conversation
            structured_llm = self.llm.with_structured_output(self.guide_info_schema)
            extracted_info = structured_llm.invoke(messages)

            # Update the guide_info object with the extracted information
            for key, value in extracted_info.items():
                if key in ["id", "name"]:
                    # Don't update these fields
                    continue
                if key == "paid_extras" and isinstance(value, dict):
                    self.guide_info.paid_extras.update(value)
                elif key == "_unanswered_questions" and isinstance(value, list):
                    self.guide_info._unanswered_questions = value
                elif value is not None:
                    setattr(self.guide_info, key, value)

            # Save the updated guide information
            self._save_guide_info()

            logger.info(f"Updated guide information for {self.guide_name}")

        except Exception as e:
            logger.error(f"Error processing guide response: {e}")

    def contact_guide(self) -> None:
        """
        Contact the guide with the user's requirements.

        Loads user information based on the user_id provided during initialization
        and creates an initial message to the guide.

        Raises:
            ValueError: If user information cannot be loaded
        """
        # Load user information
        user_info = load_user_info(self.user_id)
        if not user_info:
            raise ValueError(
                f"Could not load user information for user ID: {self.user_id}"
            )

        # Construct the message to the guide based on user requirements
        activity = user_info.get("activity", "an unspecified activity")
        location = user_info.get("location", "an unspecified location")
        start_time = user_info.get("start_time", "an unspecified time")
        participants = user_info.get("participants", "an unspecified number of people")
        user_info.get("budget", "an unspecified budget")

        message = (
            "Hello, I am a travel agent working on behalf of a client. They are"
            f" interested in: {activity} at {location}. They would like to do this"
            f" starting at {start_time} with {participants} participants. Can you help"
            " with this request? Please let me know if this is possible, what services"
            " you can provide, and your pricing. Thank you."
        )

        # Send the message to the guide
        self.guide_messenger.send(message)

        # If simulation is enabled, get the guide simulator to respond
        if self.simulation and self.guide_simulator:
            self.guide_simulator.process_and_respond()
            # Process the guide's response to update guide information
            self._process_guide_response()

    def continue_conversation(self) -> Optional[str]:
        """
        Continue the conversation with the guide.

        This method allows the user to continue interacting with the guide
        through the messenger interface.

        Returns:
            Optional[str]: A message to send to the traveler if needed, empty string
            if negotiation should pause, or None otherwise
        """
        # First, process any new responses from the guide to update guide information
        self._process_guide_response()

        # Get the user info
        user_info = load_user_info(self.user_id)

        # Get the conversation history
        conversation_history = load_conversation(self.guide_id)

        # Get the guide info
        guide_info = load_guide_info(self.guide_id)
        if not guide_info:
            raise ValueError(
                f"Could not load guide information for guide ID: {self.guide_id}"
            )

        # Define the schema for structured output
        negotiation_decision_schema = {
            "title": "NegotiationDecision",
            "description": "Decision on the next action in the negotiation process",
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "pause_negotiation",
                        "ask_traveler",
                        "talk_to_guide",
                        "end_negotiation",
                    ],
                    "description": "The action to take next in the negotiation process",
                },
                "reasoning": {
                    "type": "string",
                    "description": "Explanation for why this action was chosen",
                },
                "message": {
                    "type": "string",
                    "description": (
                        "The message to send to the guide or traveler, if applicable"
                    ),
                },
            },
            "required": ["action", "reasoning"],
        }

        # Create a structured output LLM
        structured_llm = self.llm.with_structured_output(negotiation_decision_schema)

        # Format the data using our utility functions
        formatted_user_info = format_user_info(user_info)
        formatted_guide_info = format_guide_info(guide_info)
        formatted_conversation = format_conversation_history(conversation_history)

        # Create the system message
        system_message = SystemMessage(
            content="""
            You are a travel agent negotiating with a guide on behalf of your client. Your name is Trippy.
            Your goal is to get the best possible deal for your client while ensuring
            their requirements are met. This means you always try to get the lowest price possible that meets the requirements.Make sure not to mention the budget of your client, as this is the maximum price they are willing to pay. If you mention it you won't be able to go below it. Analyze the available information and decide
            on the next action to take in the negotiation process.

            If the guide has asked a question, look good at the user information to see if you can answer it before asking the user a question. If you cannot answer it then re-phrase the question so it makes sense for the user.

            Your job is done once the next step is for the client to pay and you are convince you cannot get a better price. At this point you end the negotiation.
            """
        )

        # Create the human message with the prompt
        prompt_content = f"""
        # User Information
        ```
        {formatted_user_info}
        ```

        # Guide Information
        ```
        {formatted_guide_info}
        ```

        # Conversation History
        ```
        {formatted_conversation}
        ```

        Based on the above information, decide on the next action:
        1. "pause_negotiation" - If you need to pause the negotiation (e.g., waiting for guide response, need to consult with traveler)
        2. "ask_traveler" - If you need more information from the traveler to proceed
        3. "talk_to_guide" - If you're ready to send a message to the guide
        4. "end_negotiation" - If you've reached an agreement on the price and the next step is for the client to pay.

        Remember: You are trying to get the best deal for your client while ensuring their requirements are met. You only ask the traveler practical questions. You don't ask him about if a certain price is okay, because you always keep negotiating until you have the lowest price you think you can get. The traveler will have to accept that price.
        Try to get a price below the budget of the traveler.
        """

        # Prepare messages for the LLM
        messages = [system_message, HumanMessage(content=prompt_content)]

        # Get structured decision from LLM
        decision = structured_llm.invoke(messages)

        # Take action based on the LLM's decision
        if decision["action"] == "talk_to_guide" and decision.get("message"):
            logger.info(f"Continuing conversation with guide {self.guide_name}")
            self.guide_messenger.send(decision["message"])

            # If simulation is enabled, get the guide simulator to respond
            if self.simulation and self.guide_simulator:
                self.guide_simulator.process_and_respond()
                # Process the guide's response to update guide information
                self._process_guide_response()
            return ""

        elif decision["action"] == "ask_traveler" and decision.get("message"):
            logger.info(
                f"Guide {self.guide_name} asked traveler: {decision['message']}"
            )
            return decision["message"]

        elif decision["action"] == "pause_negotiation":
            logger.info(f"Negotiation paused for guide {self.guide_name}.")
            return ""

        elif decision["action"] == "end_negotiation":
            # Send a final thank you message to the guide
            final_message = (
                "Thank you for all the information. I'll present your offer to my"
                " client, as the client makes the final decision. We'll be in touch"
                " shortly. We appreciate your assistance."
            )
            self.guide_messenger.send(final_message)

            # Update negotiation status to completed
            self.guide_info._negotiation_status = "finished"
            self._save_guide_info()
            logger.info(f"Negotiation ended for guide {self.guide_name}.")
            return ""
        else:
            raise ValueError(
                "Unable to determine next action. Please review the conversation and"
                " try again."
            )
