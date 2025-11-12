from langchain_openai import ChatOpenAI
from agents.prompts.chat_prompts import CHAT_SYSTEM_PROMPT, CONVERSATION_PROMPT_TEMPLATE
from config import settings
from typing import Dict, Any

# Initialize LLM
llm = ChatOpenAI(
    model=settings.model_name,
    temperature=settings.temperature,
    max_tokens=settings.max_tokens,
    openai_api_key=settings.openai_api_key
)


async def generate_response(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate response using LLM"""
    user_message = state["user_message"]
    conversation_history = state.get("conversation_history", "")
    
    # Format conversation prompt
    if conversation_history:
        formatted_history = "\n".join([
            f"{msg['role'].title()}: {msg['content']}" 
            for msg in conversation_history
        ])
    else:
        formatted_history = "Esta es una nueva conversación."
    
    conversation_prompt = CONVERSATION_PROMPT_TEMPLATE.format(
        conversation_history=formatted_history,
        user_message=user_message
    )
    
    # Create messages for OpenAI
    messages = [
        {"role": "system", "content": CHAT_SYSTEM_PROMPT},
        {"role": "user", "content": conversation_prompt}
    ]
    
    # Generate response
    response = await llm.ainvoke(messages)
    
    # Update state
    state["assistant_response"] = response.content
    
    return state