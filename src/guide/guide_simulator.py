import os

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src import settings
from src.messenger.cli import CLIMessenger


class GuideSimulator:
    """
    Simulates a travel guide using an LLM.

    This class handles responding to user messages as if it were a real guide,
    generating realistic responses based on the conversation context.

    Attributes:
        guide_id: Unique identifier for the guide and the conversation to monitor
        messenger: Instance of CLIMessenger for communication
        llm: LLM client for natural language processing
    """

    def __init__(self, guide_id: str):
        """
        Initialize the GuideSimulator.

        Args:
            guide_id: The ID of the guide and conversation to monitor
        """
        self.guide_id = guide_id
        self.messenger = CLIMessenger(self.guide_id)

        # Initialize the LLM client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        model_name = settings.get("OPENAI_MODEL", None)
        if model_name is None:
            raise ValueError("OPENAI_MODEL environment variable is not set")

        self.llm = ChatOpenAI(model=model_name, temperature=0.7)

    def process_and_respond(self) -> None:
        """
        Process the latest message in the conversation and generate a response.

        This method checks the conversation history, and if there's a new message
        from the user/agent that hasn't been replied to yet, it generates a
        guide-like response and adds it to the conversation.
        """
        # Get the conversation history
        conversation_history = self.messenger.get_conversation_history()

        # If the last message is from the assistant (i.e., the guide manager/agent),
        # then we need to respond to it
        if conversation_history and conversation_history[-1]["sender"] == "assistant":
            # Create a system message for the guide persona
            system_message = SystemMessage(
                content=(
                    "You are a professional local travel guide speaking to a travel"
                    " agent. You are knowledgeable about the local area, activities,"
                    " and pricing. You should be helpful, informative, and professional"
                    " in your responses. For activities, you should provide details"
                    " about what's included, pricing, meeting points, durations, and"
                    " any special requirements. Your prices are somewhat negotiable"
                    " (10-15% max discount). Respond as if you are a real guide"
                    " responding to an inquiry about your services."
                )
            )

            # Get conversation history as langchain messages
            messages = [system_message]
            messages.extend(
                self.messenger.get_conversation_history(as_langchain_messages=True)
            )

            # Generate response
            response = self.llm.invoke(messages)

            # Send the response as coming from the guide, not the assistant
            self.messenger.send(response.content, sender="guide")
