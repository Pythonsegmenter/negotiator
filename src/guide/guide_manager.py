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

        # Create a guide simulator if needed
        self.guide_simulator = GuideSimulator(self.guide_id) if simulation else None

    def _save_guide_info(self) -> None:
        """Save the guide information to a file."""
        guide_info_dict = asdict(self.guide_info)
        save_guide_info(guide_info_dict)

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
        budget = user_info.get("budget", "an unspecified budget")

        message = (
            "Hello, I am a travel agent working on behalf of a client. They are"
            f" interested in: {activity} at {location}. They would like to do this"
            f" starting at {start_time} with {participants} participants. Their budget"
            f" is {budget}. Can you help with this request? Please let me know if this"
            " is possible, what services you can provide, and your pricing. Thank you."
        )

        # Send the message to the guide
        self.guide_messenger.send(message)

        # If simulation is enabled, get the guide simulator to respond
        if self.simulation and self.guide_simulator:
            self.guide_simulator.process_and_respond()

    def continue_conversation(self) -> Optional[str]:
        """
        Continue the conversation with the guide.

        This method allows the user to continue interacting with the guide
        through the messenger interface.

        Returns:
            Optional[str]: A message to send to the traveler if needed, empty string
            if negotiation should pause, or None otherwise
        """

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
                    "enum": ["pause_negotiation", "ask_traveler", "talk_to_guide"],
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
            You are a travel agent negotiating with a guide on behalf of your client.
            Your goal is to get the best possible deal for your client while ensuring
            their requirements are met. Analyze the available information and decide
            on the next action to take in the negotiation process.

            If the guide has asked a question, look good at the user information to see if you can answer it before asking the user a question.
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

        Remember: You are trying to get the best deal for your client while ensuring their requirements are met. You only ask the traveler practical questions. You don't ask him about if a certain price is okay, because you always keep negotiating until you have the lowest price you think you can get. The traveler will have to accept that price.
        """

        # Prepare messages for the LLM
        messages = [system_message, HumanMessage(content=prompt_content)]

        # Get structured decision from LLM
        decision = structured_llm.invoke(messages)

        # Take action based on the LLM's decision
        if decision["action"] == "talk_to_guide" and decision.get("message"):
            logger.info(f"Continuing conversation with guide {self.guide_name}")
            self.guide_messenger.send(decision["message"])
            logger.info(f"Message sent to guide: {decision['message']}")

            # If simulation is enabled, get the guide simulator to respond
            if self.simulation and self.guide_simulator:
                self.guide_simulator.process_and_respond()
            return ""

        elif decision["action"] == "ask_traveler" and decision.get("message"):
            logger.info(
                f"Guide {self.guide_name} asked traveler: {decision['message']}"
            )
            return decision["message"]

        elif decision["action"] == "pause_negotiation":
            return ""

        else:
            raise ValueError(
                "Unable to determine next action. Please review the conversation and"
                " try again."
            )
