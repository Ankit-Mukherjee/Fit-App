from db import fitness_profiles_collection, fitness_notes_collection, get_embedding
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)


def get_default_profile(user_id):
    return {
        "_id": user_id,
        "general": {
            "name": "",
            "age": 30,
            "weight": 70,
            "height": 170,
            "activity_level": "Moderately Active",
            "gender": "Male"
        },
        "goals": ["Muscle Gain"],
        "nutrition": {
            "calories": 2000,
            "protein": 140,
            "fat": 65,
            "carbs": 200,
        },
    }


def create_profile(user_id: str) -> Dict[str, Any]:
    profile_values = get_default_profile(user_id)
    result = fitness_profiles_collection.insert_one(profile_values)
    profile_values['_id'] = str(result['id'])  # Use the returned ID
    return profile_values


def get_profile(user_id: str) -> Optional[Dict[str, Any]]:
    return fitness_profiles_collection.find_one({"_id": user_id})


def update_profile(user_id: str, update_field: str, **kwargs) -> Dict[str, Any]:
    existing = get_profile(user_id)
    if not existing:
        existing = create_profile(user_id)
    
    if update_field == "goals":
        existing["goals"] = kwargs.get("goals", [])
        update_data = {"goals": existing["goals"]}
    elif update_field == "nutrition":
        existing["nutrition"].update(kwargs)
        update_data = {"nutrition": existing["nutrition"]}
    else:
        existing[update_field].update(kwargs)
        update_data = {update_field: existing[update_field]}

    fitness_profiles_collection.update_one(
        {"_id": user_id},  # Filter by ID
        {"$set": update_data}
    )
    return existing


def get_notes(user_id: str) -> List[Dict[str, Any]]:
    try:
        notes = fitness_notes_collection.find({"user_id": user_id})
        # Convert each note to a dictionary, handling the AstraDB response format
        result_notes = []
        for note in notes:
            if isinstance(note, dict):
                result_notes.append(note)
            else:
                # If it's not already a dict, try to convert it
                try:
                    result_notes.append(dict(note))
                except Exception:
                    # If conversion fails, try to get the raw data
                    result_notes.append({"text": str(note)})
        return result_notes
    except Exception as e:
        logger.error(f"Failed to get notes: {str(e)}")
        return []


def add_note(note_text: str, user_id: str) -> Dict[str, Any]:
    # Create the document with $vectorize field for automatic NVIDIA embedding
    new_note = {
        "user_id": user_id,
        "text": note_text,
        "metadata": {"ingested": datetime.now().isoformat()},
        "$vectorize": note_text  # AstraDB will automatically create NVIDIA embedding
    }
    
    try:
        # Insert the note
        result = fitness_notes_collection.insert_one(new_note)
        
        if isinstance(result, dict):
            # Check for the nested status structure with insertedIds
            if 'status' in result and 'insertedIds' in result['status']:
                inserted_id = result['status']['insertedIds'][0]
                new_note['_id'] = inserted_id
                logger.info(f"Successfully inserted note with ID: {inserted_id}")
                return new_note
            else:
                logger.error(f"Unexpected response format from AstraDB: {result}")
        
        # If we get here, something went wrong
        raise ValueError("Failed to get insertion confirmation from AstraDB")
    except Exception as e:
        logger.error(f"Error saving note: {str(e)}")
        raise ValueError(f"Failed to save note: {str(e)}")


def delete_note(note_id: str) -> bool:
    result = fitness_notes_collection.delete_one(note_id)  # Pass ID directly
    return result['status_code'] == 200  # Check if deletion was successful


def search_similar_notes(search_text: str, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
    """
    Perform semantic vector search to find similar notes for a user.
    Returns top N most relevant notes based on vector similarity.
    """
    try:
        # Use the $vectorize operator in the find command for automatic NVIDIA embedding
        all_results = fitness_notes_collection.find(
            filter={"user_id": user_id},
            sort={"$vectorize": search_text}  # AstraDB will handle embedding and similarity search
        )
        # Manually limit results since we can't use limit parameter
        # Convert results to list and take only the first 'limit' items
        results = []
        for note in all_results:
            if len(results) >= limit:
                break
            results.append(note)
        return results
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        return []

