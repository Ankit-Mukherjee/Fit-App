from db import fitness_profiles_collection, fitness_notes_collection
from datetime import datetime


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


def create_profile(user_id):
    profile_values = get_default_profile(user_id)
    result = fitness_profiles_collection.insert_one(profile_values)
    return result.inserted_id, profile_values


def get_profile(user_id):
    return fitness_profiles_collection.find_one({"_id": {"$eq": user_id}})


def update_profile(user_id, update_field, **kwargs):
    existing = get_profile(user_id)
    if not existing:
        user_id, existing = create_profile(user_id)
    
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
        {"_id": user_id}, {"$set": update_data}
    )
    return existing


def get_notes(user_id):
    return list(fitness_notes_collection.find({"user_id": {"$eq": user_id}}))


def add_note(note_text, user_id):
    new_note = {
        "user_id": user_id,
        "text": note_text,
        "$vectorize": note_text,
        "metadata": {"ingested": datetime.now().isoformat()},
    }
    result = fitness_notes_collection.insert_one(new_note)
    new_note["_id"] = result.inserted_id
    return new_note


def delete_note(note_id):
    return fitness_notes_collection.delete_one({"_id": note_id})


def search_similar_notes(search_text, user_id, limit=3):
    """
    Perform semantic vector search to find similar notes for a user.
    Returns top N most relevant notes based on vector similarity.
    """
    try:
        # Vector similarity search: filter by user_id and sort by semantic similarity
        results = fitness_notes_collection.find(
            filter={"user_id": {"$eq": user_id}},
            sort={"$vectorize": search_text},
            limit=limit,
            include_similarity=True,
        )
        return list(results)
    except Exception:
        # Fallback to empty list if vector search fails
        return []

