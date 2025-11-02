import os
from typing import Any, Dict, Optional
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from AI import get_macro_plan, get_workout_recommendation
from profiles import (
    create_profile,
    get_profile,
    update_profile,
    get_notes,
    add_note,
    delete_note,
    search_similar_notes,
)


load_dotenv()


def _profile_dict_to_string(profile: Dict[str, Any]) -> str:
    segments = []
    name = profile.get("name")
    if name:
        segments.append(f"Name: {name}")
    age = profile.get("age")
    if age:
        segments.append(f"Age {age}")
    gender = profile.get("gender")
    if gender:
        segments.append(f"Gender {gender}")
    height = profile.get("height")
    if height:
        segments.append(f"Height {height} cm")
    weight = profile.get("weight")
    if weight:
        segments.append(f"Weight {weight} kg")
    body_fat = profile.get("bodyFat")
    if body_fat:
        segments.append(f"Body fat {body_fat} %")
    activity = profile.get("activity")
    if activity:
        segments.append(f"Activity level {activity}")
    goal = profile.get("goal")
    if goal:
        segments.append(f"Primary goal {goal}")

    extras = {
        key: value
        for key, value in profile.items()
        if key
        not in {
            "name",
            "age",
            "gender",
            "height",
            "weight",
            "bodyFat",
            "activity",
            "goal",
        }
        and value not in ("", None)
    }
    for key, value in extras.items():
        segments.append(f"{key}: {value}")

    return ", ".join(segments) if segments else "No profile details provided"


class MacroPlanRequest(BaseModel):
    goal: str = Field(..., description="Primary nutrition goal, e.g. build muscle")
    profile: Dict[str, Any] = Field(
        default_factory=dict, description="Dictionary of profile attributes"
    )


class AdviceRequest(BaseModel):
    question: str = Field(..., description="User's training or nutrition question")
    profileSummary: Optional[str] = Field(
        default=None,
        description="Preformatted profile summary string; optional",
    )
    profile: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional profile dictionary to build summary if not provided",
    )
    userId: Optional[str] = Field(
        default=None, description="Optional user ID for RAG-enhanced advice from saved notes"
    )


class ProfileRequest(BaseModel):
    userId: Optional[str] = Field(default=None, description="User ID for profile operations")
    general: Optional[Dict[str, Any]] = Field(default=None, description="General profile data")
    goals: Optional[list] = Field(default=None, description="User goals")
    nutrition: Optional[Dict[str, Any]] = Field(default=None, description="Nutrition data")


class NoteRequest(BaseModel):
    userId: str = Field(..., description="User ID")
    text: str = Field(..., description="Note text")


class NoteDeleteRequest(BaseModel):
    noteId: str = Field(..., description="Note ID to delete")


app = FastAPI(title="FitFlow AI API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/macro-plan")
def macro_plan_endpoint(request: MacroPlanRequest) -> Dict[str, str]:
    try:
        profile_str = _profile_dict_to_string(request.profile)
        plan = get_macro_plan(goal=request.goal, profile=profile_str)
        return {"text": plan}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail="Macro plan generation failed") from exc


@app.post("/workout-advice")
def workout_advice_endpoint(request: AdviceRequest) -> Dict[str, str]:
    try:
        # Log the incoming request
        print(f"Received workout advice request:")
        print(f"Question: {request.question}")
        print(f"Profile Summary: {request.profileSummary}")
        print(f"User ID: {request.userId}")
        
        # Get or generate profile summary
        if request.profileSummary:
            profile_summary = request.profileSummary
            print(f"Using provided profile summary: {profile_summary}")
        elif request.profile is not None:
            profile_summary = _profile_dict_to_string(request.profile)
            print(f"Generated profile summary: {profile_summary}")
        else:
            profile_summary = ""
            print("No profile information provided")

        # RAG: Search for relevant context from user's saved notes
        context = ""
        if request.userId:
            try:
                similar_notes = search_similar_notes(
                    search_text=request.question, user_id=request.userId, limit=3
                )
                if similar_notes:
                    context_parts = [
                        f"- {note.get('text', '')}" for note in similar_notes if note.get('text')
                    ]
                    if context_parts:
                        context = "\n\n**Relevant context from your notes:**\n" + "\n".join(
                            context_parts
                        )
                        print(f"Found relevant context from notes: {context}")
            except Exception as note_error:
                print(f"Error searching notes (non-critical): {str(note_error)}")
                # Continue without notes context if there's an error

        # Add context to the question for enhanced AI advice
        enhanced_question = request.question + context if context else request.question
        print(f"Enhanced question with context: {enhanced_question}")

        # Get the workout recommendation
        try:
            advice_text = get_workout_recommendation(
                profile=profile_summary,
                question=enhanced_question,
            )
            print(f"Successfully generated advice: {advice_text[:100]}...")  # First 100 chars
            return {"text": advice_text}
        except Exception as advice_error:
            print(f"Error getting workout recommendation: {str(advice_error)}")
            print(f"Profile summary used: {profile_summary}")
            print(f"Enhanced question used: {enhanced_question}")
            raise
            
    except ValueError as exc:
        print(f"Validation error in workout advice: {str(exc)}")
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Unexpected error in workout advice: {str(exc)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Advice generation failed: {str(exc)}"
        ) from exc


@app.get("/profile/{user_id}")
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """Retrieve a user's complete fitness profile."""
    try:
        profile = get_profile(user_id)
        if not profile:
            user_id, profile = create_profile(user_id)
        return {"userId": user_id, "profile": profile}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to retrieve profile: {exc}") from exc


@app.post("/profile")
def create_or_update_profile(request: ProfileRequest) -> Dict[str, Any]:
    """Create or update a user's fitness profile."""
    try:
        user_id = request.userId or str(uuid4())
        existing = get_profile(user_id)
        if not existing:
            user_id, existing = create_profile(user_id)

        update_data = {}
        if request.general is not None:
            update_data["general"] = request.general
        if request.goals is not None:
            update_data["goals"] = request.goals
        if request.nutrition is not None:
            update_data["nutrition"] = request.nutrition

        if update_data:
            updated = update_profile(user_id, list(update_data.keys())[0], **list(update_data.values())[0])
        else:
            updated = existing

        return {"userId": user_id, "profile": updated}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {exc}") from exc


@app.get("/notes/{user_id}")
def get_user_notes(user_id: str) -> Dict[str, Any]:
    """Retrieve all notes for a user."""
    try:
        notes = get_notes(user_id)
        return {"userId": user_id, "notes": notes}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to retrieve notes: {exc}") from exc


@app.post("/notes")
def create_note(request: NoteRequest) -> Dict[str, Any]:
    """Create a new note for a user."""
    try:
        note = add_note(request.text, request.userId)
        if not note:
            raise ValueError("Note creation returned no data")
        return {"note": note}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pylint: disable=broad-except
        # Log the full error for debugging
        import traceback
        print(f"Note creation error: {exc}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(exc)}") from exc


@app.delete("/notes/{note_id}")
def delete_user_note(note_id: str) -> Dict[str, str]:
    """Delete a note by ID."""
    try:
        delete_note(note_id)
        return {"status": "deleted", "noteId": note_id}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Failed to delete note: {exc}") from exc


@app.post("/notes/search")
def search_notes(request: Dict[str, Any]) -> Dict[str, Any]:
    """Search for notes using vector similarity search."""
    try:
        user_id = request.get("userId")
        query = request.get("query", "")
        limit = request.get("limit", 5)

        if not user_id:
            raise HTTPException(status_code=400, detail="userId is required")

        results = search_similar_notes(search_text=query, user_id=user_id, limit=limit)
        return {"results": results, "count": len(results)}
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(
        "app:app",
        host=os.environ.get("UVICORN_HOST", "0.0.0.0"),
        port=int(os.environ.get("UVICORN_PORT", 8000)),
        reload=os.environ.get("UVICORN_RELOAD", "true").lower() == "true",
    )