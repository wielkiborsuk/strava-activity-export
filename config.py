import os
from google.cloud import secretmanager
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# Global variable to store Secret Manager client
_secret_client = None

def get_secret_client():
    """Lazily initializes the Secret Manager client."""
    global _secret_client
    if _secret_client is None:
        _secret_client = secretmanager.SecretManagerServiceClient()
    return _secret_client

def get_secret(secret_id):
    """Retrieves secret from environment variable (local) or Secret Manager (GCP)."""
    # Check local environment first
    local_secret = os.environ.get(secret_id)
    if local_secret:
        return local_secret

    # Fallback to GCP Secret Manager
    project_id = os.environ.get('GCP_PROJECT')
    if not project_id:
        raise ValueError(f"Secret {secret_id} not found in environment and GCP_PROJECT is not set.")
    
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        client = get_secret_client()
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_id} in GCP: {e}")
        raise

def update_secret(secret_id, new_value):
    """Updates a secret in Secret Manager (or logs to console locally)."""
    project_id = os.environ.get('GCP_PROJECT')
    
    if not project_id:
        print(f"Local development: new value for {secret_id} is provided. Update your .env file manually.")
        return

    parent = f"projects/{project_id}/secrets/{secret_id}"
    payload = new_value.encode("UTF-8")
    client = get_secret_client()
    try:
        client.add_secret_version(
            request={"parent": parent, "payload": {"data": payload}}
        )
        print(f"Updated GCP Secret Manager secret: {secret_id}")
    except Exception as e:
        print(f"Failed to update GCP secret {secret_id}: {e}")
