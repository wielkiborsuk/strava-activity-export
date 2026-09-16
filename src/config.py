import os
from firebase_admin import initialize_app, firestore
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Global variable to store initialized Firebase app status
_firebase_initialized = False
_firestore_client = None

def _get_firestore_client():
    """Initializes Firebase Admin SDK and returns Firestore client."""
    global _firebase_initialized, _firestore_client
    if not _firebase_initialized:
        try:
            # Firestore client automatically uses GCP_PROJECT or ADC
            initialize_app()
        except ValueError:
            # App already initialized
            pass
        _firebase_initialized = True
    
    if _firestore_client is None:
        _firestore_client = firestore.client()
    
    return _firestore_client

def get_secret(secret_id):
    """Retrieves config/secret from environment variable (local) or Firestore."""
    # Check local environment first
    local_secret = os.environ.get(secret_id)
    if local_secret:
        return local_secret

    db = _get_firestore_client()

    try:
        # We store secrets in a 'config' collection, in a 'secrets' document
        # This provides a flat key-value structure within that document
        doc_ref = db.collection('config').document('secrets')
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            value = data.get(secret_id)
            if value is not None:
                return str(value)
        
        raise ValueError(f"Config {secret_id} not found in Firestore (config/secrets).")
    except Exception as e:
        print(f"Error accessing config {secret_id} in Firestore: {e}")
        raise

def update_secret(secret_id, new_value):
    """Updates a parameter in Firestore (or logs to console locally)."""
    # Check if we are running locally
    project_id = os.environ.get('GCP_PROJECT')

    if not project_id:
        print(f"Local development: new value for {secret_id} is provided. Update your .env file manually.")
        return

    db = _get_firestore_client()

    try:
        doc_ref = db.collection('config').document('secrets')
        # Use merge=True to only update/add the specific secret_id field
        doc_ref.set({secret_id: new_value}, merge=True)
        print(f"Updated Firestore config: {secret_id}")
    except Exception as e:
        print(f"Failed to update Firestore config {secret_id}: {e}")
