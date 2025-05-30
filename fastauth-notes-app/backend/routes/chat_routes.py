from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx
import os
from typing import List, Optional

from ..auth import get_current_active_user
from ..database import get_database

chat_router = APIRouter()

# Get Groq API key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    emotion: str


@chat_router.post("/chat", response_model=ChatResponse)
async def emotional_chat(request: ChatRequest, current_user=Depends(get_current_active_user)):
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Groq API key not configured"
        )
    
    # Prepare conversation history
    messages = request.conversation_history.copy() if request.conversation_history else []
    
    # Add system message for emotional awareness
    if not any(msg.role == "system" for msg in messages):
        system_message = ChatMessage(
            role="system",
            content="You are an emotionally intelligent assistant. Analyze the user's message for emotional tone and respond appropriately. "
                    "Include an emotion tag at the end of your response in the format [EMOTION: emotion_name]. "
                    "Be empathetic and supportive."
        )
        messages.append(system_message)
    
    # Add user's current message
    messages.append(ChatMessage(role="user", content=request.message))
    
    # Prepare the request to Groq API
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama3-8b-8192",  # Using Llama 3 model
        "messages": [{
            "role": msg.role,
            "content": msg.content
        } for msg in messages],
        "temperature": 0.7,
        "max_tokens": 800
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(GROQ_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            
            # Extract the assistant's message
            assistant_message = response_data["choices"][0]["message"]["content"]
            
            # Extract emotion tag if present
            emotion = "neutral"
            import re
            emotion_match = re.search(r"\[EMOTION:\s*([^\]]+)\]", assistant_message)
            if emotion_match:
                emotion = emotion_match.group(1).strip()
                # Remove the emotion tag from the message
                assistant_message = re.sub(r"\[EMOTION:\s*[^\]]+\]", "", assistant_message).strip()
            
            return {
                "message": assistant_message,
                "emotion": emotion
            }
    
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error from Groq API: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process chat: {str(e)}"
        )


@chat_router.post("/save-conversation", status_code=status.HTTP_201_CREATED)
async def save_conversation(conversation: List[ChatMessage], current_user=Depends(get_current_active_user), db=Depends(get_database)):
    """Save a conversation history to the database"""
    conversations_collection = db.conversations
    
    conversation_data = {
        "user_id": current_user["_id"],
        "messages": [{
            "role": msg.role,
            "content": msg.content
        } for msg in conversation],
        "created_at": datetime.utcnow()
    }
    
    result = await conversations_collection.insert_one(conversation_data)
    
    return {"id": str(result.inserted_id)}


@chat_router.get("/conversations", response_model=List[dict])
async def get_conversations(current_user=Depends(get_current_active_user), db=Depends(get_database)):
    """Get all conversations for the current user"""
    conversations_collection = db.conversations
    
    conversations = await conversations_collection.find({"user_id": current_user["_id"]}).to_list(length=100)
    
    # Convert ObjectId to string
    for conv in conversations:
        conv["id"] = str(conv["_id"])
        del conv["_id"]
    
    return conversations