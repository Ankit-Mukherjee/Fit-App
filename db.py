from typing import Optional
import astrapy.db
from astrapy.db import AstraDB
from dotenv import load_dotenv
import os
import logging

load_dotenv()

ENDPOINT = os.getenv("ASTRA_DB_API_ENDPOINT")
TOKEN = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
KEYSPACE = os.getenv("ASTRA_DB_KEYSPACE", "default_keyspace")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_embedding(text):
    """Get NVIDIA embedding for the given text."""
    # The $vectorize operator in AstraDB will automatically use NVIDIA embeddings
    # We just need to return the text and AstraDB will handle the embedding
    return text

def get_db():
    if not TOKEN or not ENDPOINT:
        raise ValueError("Missing required environment variables: ASTRA_DB_APPLICATION_TOKEN or ASTRA_DB_API_ENDPOINT")
    try:
        client = AstraDB(
            token=TOKEN,
            api_endpoint=ENDPOINT
        )
        # Test the connection
        info = client.get_collections()
        logger.info(f"Successfully connected to AstraDB. Collections: {info}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to AstraDB: {str(e)}")
        raise

try:
    db = get_db()
    
    # Initialize fitness_profiles collection (non-vector)
    try:
        fitness_profiles_collection = db.collection("fitness_profiles")
        fitness_profiles_collection.find_one({})
        logger.info("Collection 'fitness_profiles' exists and is accessible")
    except Exception as e:
        logger.info("Creating collection 'fitness_profiles'...")
        db.create_collection("fitness_profiles")
        fitness_profiles_collection = db.collection("fitness_profiles")
        logger.info("Collection 'fitness_profiles' created successfully")

    # Initialize notes collection with vector search
    try:
        notes_collection = db.collection("notes")
        notes_collection.find_one({})  # Test if collection exists
        logger.info("Collection 'notes' exists and is accessible")
    except Exception as e:
        logger.info("Creating collection 'notes' with vector search...")
        db.create_collection(
            "notes",
            options={
                "vector": {
                    "dimension": 1024,  # NVIDIA embedding dimension
                    "metric": "cosine"
                }
            }
        )
        notes_collection = db.collection("notes")
        logger.info("Collection 'notes' created successfully with vector search")

except Exception as e:
    logger.error(f"Failed to initialize database and collections: {str(e)}")
    raise

# Export the collections
fitness_profiles_collection = fitness_profiles_collection
fitness_notes_collection = notes_collection
fitness_notes_collection = db.collection("notes")
