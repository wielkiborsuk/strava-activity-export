import os
import requests
import json
from google.cloud import secretmanager
import functions_framework
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
    # Check if the secret is available in environment variables first (for local dev)
    local_secret = os.environ.get(secret_id)
    if local_secret:
        return local_secret

    project_id = os.environ.get('GCP_PROJECT')
    if not project_id:
        raise ValueError("Neither local environment variable nor GCP_PROJECT is set")

    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    try:
        client = get_secret_client()
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        print(f"Error accessing secret {secret_id}: {e}")
        raise

def update_refresh_token(secret_id, new_token):
    project_id = os.environ.get('GCP_PROJECT')

    if not project_id:
        print(f"Local development: new refresh token is {new_token}. Update your .env file manually.")
        return

    parent = f"projects/{project_id}/secrets/{secret_id}"

    # For simplicity, we just add a new version
    payload = new_token.encode("UTF-8")
    client = get_secret_client()
    client.add_secret_version(
        request={"parent": parent, "payload": {"data": payload}}
    )
    print(f"Updated secret {secret_id} with new refresh token.")

def get_strava_access_token():
    """Refreshes the Strava access token using the stored refresh token."""
    client_id = get_secret("STRAVA_CLIENT_ID")
    client_secret = get_secret("STRAVA_CLIENT_SECRET")
    refresh_token = get_secret("STRAVA_REFRESH_TOKEN")

    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "scope": "activity:read_permission"
        }
    )

    if response.status_code != 200:
        print(f"Error refreshing token: {response.text}")
        response.raise_for_status()

    token_data = response.json()
    print(token_data)

    # If a new refresh token is provided, update it in Secret Manager
    if "refresh_token" in token_data and token_data["refresh_token"] != refresh_token:
        try:
            update_refresh_token("STRAVA_REFRESH_TOKEN", token_data["refresh_token"])
        except Exception as e:
            print(f"Failed to update refresh token in Secret Manager: {e}")
            # We can still proceed since the current access_token is valid

    return token_data["access_token"]

@functions_framework.http
def extract_strava_activities(request):
    """
    HTTP Cloud Function entry point.
    Extracts activities from Strava API.
    """
    try:
        access_token = get_strava_access_token()
        print(access_token)

        # Headers for API call
        headers = {"Authorization": f"Bearer {access_token}"}

        # You can customize these params based on request arguments
        params = {
            "per_page": request.args.get("per_page", 30),
            "page": request.args.get("page", 1)
        }

        activities_url = "https://www.strava.com/api/v3/athlete/activities"

        print(f"Fetching activities with params: {params}")
        response = requests.get(activities_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f"Strava API error: {response.text}")
            return (
                json.dumps({"error": "Failed to fetch activities from Strava", "details": response.text}),
                response.status_code,
                {"Content-Type": "application/json"}
            )

        activities = response.json()

        return (
            json.dumps(activities),
            200,
            {"Content-Type": "application/json"}
        )

    except Exception as e:
        print(f"Unhandled exception: {e}")
        return (
            json.dumps({"error": str(e)}),
            500,
            {"Content-Type": "application/json"}
        )
