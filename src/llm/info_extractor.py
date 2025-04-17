"""
Information extraction module for analyzing user conversations.

This module provides functionality to extract user information from conversations
and identify if new information is present compared to existing user data.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict
from src.user_manager import UserInfo


def generate_info_extraction_prompt(
    current_user_info: Optional[UserInfo],
    conversation_history: List[Dict[str, str]]
) -> str:
    """
    Generate a prompt for an LLM to extract user information from conversations.
    
    This creates a structured prompt instructing the LLM to identify new or changed
    information in the conversation compared to existing user data.
    
    Args:
        current_user_info: Current known user information, or None if no information exists yet
        conversation_history: List of conversation messages, each with "sender" and "text" keys
        
    Returns:
        str: A formatted prompt for the LLM
    """
    # Convert UserInfo to dictionary if it exists
    current_info_dict = asdict(current_user_info) if current_user_info else {}
    
    # Format the conversation history as a dialogue
    formatted_conversation = "\n".join([
        f"{msg['sender']}: {msg['text']}" 
        for msg in conversation_history
    ])
    
    # Create the main prompt
    prompt = f"""
# Information Extraction Task

## Current User Information
```json
{current_info_dict}
```

## Conversation History
{formatted_conversation}

## Task
1. Analyze the conversation history to identify any new information about the user's travel plans.
2. Check if the user has provided information about any of these fields that we don't currently have, or has changed information we already have:
   - activity: What activity they want to do
   - location: Where the activity takes place 
   - start_time: When the activity starts (ISO format with timezone if possible)
   - deadline_negotation: Deadline for completing negotiations (ISO format with timezone if possible)
   - participants: Number of people participating
   - budget: Maximum budget for the activity
   - preferences: Any specific preferences like price_vs_value ("lowest_price" or "best_value")

## Output Format
Return a JSON object with these fields:
- "found_new_info": Boolean indicating if any new information was found
- "new_info": An object containing only the new or changed fields
- "reasoning": Brief explanation of what new information was detected and from which messages

If no new information is found, return:
{{
  "found_new_info": false,
  "new_info": {{}},
  "reasoning": "No new information detected in the conversation."
}}
"""
    
    return prompt


def extract_user_info_from_response(
    llm_response: str
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Parse the LLM's response to extract structured information.
    
    Args:
        llm_response: The raw text response from the LLM
        
    Returns:
        Tuple containing:
            - Boolean indicating if new information was found
            - Dictionary of new/updated information fields
            - String with the reasoning/explanation
    """
    # This is a placeholder for actual JSON parsing logic
    # In a real implementation, you would use json.loads() with proper error handling
    # and validation against the expected format
    
    # Placeholder implementation
    try:
        import json
        response_data = json.loads(llm_response)
        
        return (
            response_data.get("found_new_info", False),
            response_data.get("new_info", {}),
            response_data.get("reasoning", "No reasoning provided.")
        )
    except json.JSONDecodeError:
        # Fallback behavior if parsing fails
        return False, {}, "Failed to parse LLM response as JSON." 