"""
LLM service module for handling interactions with language models.

This module provides a service layer for making requests to language models
and processing their responses for various application functions.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from src.user_manager import UserInfo
from src.llm.info_extractor import generate_info_extraction_prompt, extract_user_info_from_response

# Set up logging
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with language models.
    
    This class handles communication with language models, providing a clean
    interface for various LLM-based tasks such as information extraction.
    """
    
    def __init__(self, model_name: str = "gpt-4", api_key: Optional[str] = None):
        """
        Initialize the LLM service.
        
        Args:
            model_name: The name/identifier of the LLM to use
            api_key: Optional API key for the LLM provider
        """
        self.model_name = model_name
        self.api_key = api_key
        # This would be replaced with actual LLM client initialization
        # e.g., from openai import OpenAI
        # self.client = OpenAI(api_key=api_key)
        
    def _send_prompt_to_llm(self, prompt: str) -> str:
        """
        Send a prompt to the language model and get the response.
        
        Args:
            prompt: The prompt text to send to the LLM
            
        Returns:
            str: The LLM's response text
            
        Raises:
            Exception: If there's an error communicating with the LLM
        """
        # This is a placeholder for the actual API call
        # In a real implementation, you would:
        # 1. Call the appropriate API (OpenAI, Anthropic, etc.)
        # 2. Handle retries and errors
        # 3. Process and return the response
        
        logger.debug(f"Sending prompt to {self.model_name}")
        
        # Placeholder implementation - replace with actual API call
        try:
            # Example implementation for OpenAI:
            # response = self.client.chat.completions.create(
            #     model=self.model_name,
            #     messages=[{"role": "user", "content": prompt}],
            #     temperature=0.1  # Low temperature for factual extraction
            # )
            # return response.choices[0].message.content
            
            # For now, return a mock response
            return '{"found_new_info": false, "new_info": {}, "reasoning": "Mock response"}'
        except Exception as e:
            logger.error(f"Error calling LLM: {str(e)}")
            raise
    
    def extract_user_info(
        self, 
        current_user_info: Optional[UserInfo],
        conversation_history: List[Dict[str, str]]
    ) -> Tuple[bool, Dict[str, Any], str]:
        """
        Extract user information from conversation history.
        
        This method analyzes the conversation to identify any new or updated
        information about the user's travel plans compared to what we already know.
        
        Args:
            current_user_info: Current known user information, or None if no information exists yet
            conversation_history: List of conversation messages with "sender" and "text" keys
            
        Returns:
            Tuple containing:
                - Boolean indicating if new information was found
                - Dictionary of new/updated information fields
                - String with the reasoning/explanation
        """
        # Generate the prompt for information extraction
        prompt = generate_info_extraction_prompt(current_user_info, conversation_history)
        
        # Send the prompt to the LLM
        llm_response = self._send_prompt_to_llm(prompt)
        
        # Process the LLM's response
        return extract_user_info_from_response(llm_response) 