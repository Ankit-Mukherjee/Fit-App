from astrapy.client import DataAPIClient
from dotenv import load_dotenv
import os

load_dotenv()

ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")


def get_db():
    if not TOKEN or not ENDPOINT:
        raise ValueError("Missing required environment variables: ASTRA_DB_APPLICATION_TOKEN or ASTRA_DB_API_ENDPOINT")
    client = DataAPIClient(token=TOKEN)
    db = client.get_database_by_api_endpoint(api_endpoint=ENDPOINT)
    return db


db = get_db()
collection_names = ["fitness_profiles", "notes"]

for collection in collection_names:
    try:
        db.create_collection(collection)
    except Exception:
        pass

fitness_profiles_collection = db.get_collection("fitness_profiles")
fitness_notes_collection = db.get_collection("notes")
