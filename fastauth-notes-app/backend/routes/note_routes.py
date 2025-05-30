from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from ..auth import get_current_active_user
from ..database import get_database

notes_router = APIRouter()


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class NoteResponse(BaseModel):
    id: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            ObjectId: lambda v: str(v)
        }


@notes_router.get("/", response_model=List[NoteResponse])
async def get_notes(current_user=Depends(get_current_active_user), db=Depends(get_database)):
    notes_collection = db.notes
    notes = await notes_collection.find({"user_id": current_user["_id"]}).to_list(length=100)
    
    # Convert ObjectId to string for each note
    for note in notes:
        note["id"] = str(note["_id"])
    
    return notes


@notes_router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(note: NoteCreate, current_user=Depends(get_current_active_user), db=Depends(get_database)):
    notes_collection = db.notes
    
    now = datetime.utcnow()
    new_note = {
        "title": note.title,
        "content": note.content,
        "user_id": current_user["_id"],
        "created_at": now,
        "updated_at": now
    }
    
    result = await notes_collection.insert_one(new_note)
    
    # Get the created note
    created_note = await notes_collection.find_one({"_id": result.inserted_id})
    created_note["id"] = str(created_note["_id"])
    
    return created_note


@notes_router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: str, current_user=Depends(get_current_active_user), db=Depends(get_database)):
    notes_collection = db.notes
    
    try:
        note = await notes_collection.find_one({"_id": ObjectId(note_id), "user_id": current_user["_id"]})
    except:
        raise HTTPException(status_code=400, detail="Invalid note ID format")
    
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note["id"] = str(note["_id"])
    return note


@notes_router.put("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: str, note: NoteUpdate, current_user=Depends(get_current_active_user), db=Depends(get_database)):
    notes_collection = db.notes
    
    try:
        existing_note = await notes_collection.find_one({"_id": ObjectId(note_id), "user_id": current_user["_id"]})
    except:
        raise HTTPException(status_code=400, detail="Invalid note ID format")
    
    if existing_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    update_data = {k: v for k, v in note.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await notes_collection.update_one({"_id": ObjectId(note_id)}, {"$set": update_data})
    
    updated_note = await notes_collection.find_one({"_id": ObjectId(note_id)})
    updated_note["id"] = str(updated_note["_id"])
    
    return updated_note


@notes_router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str, current_user=Depends(get_current_active_user), db=Depends(get_database)):
    notes_collection = db.notes
    
    try:
        existing_note = await notes_collection.find_one({"_id": ObjectId(note_id), "user_id": current_user["_id"]})
    except:
        raise HTTPException(status_code=400, detail="Invalid note ID format")
    
    if existing_note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    
    await notes_collection.delete_one({"_id": ObjectId(note_id)})
    
    return None