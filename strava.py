import requests
import datetime
import time

def refresh_access_token(client_id, client_secret, refresh_token):
    """
    Refreshes the Strava access token.
    Returns the full JSON response from Strava.
    """
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Error refreshing Strava token: {response.text}")
    
    return response.json()

def get_access_token(client_id, client_secret, refresh_token, on_token_refresh=None):
    """
    Orchestrates getting a valid access token.
    If a new refresh token is issued, the on_token_refresh callback is called.
    """
    token_data = refresh_access_token(client_id, client_secret, refresh_token)
    
    new_refresh_token = token_data.get("refresh_token")
    if on_token_refresh and new_refresh_token and new_refresh_token != refresh_token:
        on_token_refresh(new_refresh_token)
        
    return token_data["access_token"]

def map_activity(activity):
    """
    Maps a raw Strava activity to the requested subset of fields.
    """
    return {
        "name": activity.get("name"),
        "distance": activity.get("distance"),
        "moving_time": activity.get("moving_time"),
        "elapsed_time": activity.get("elapsed_time"),
        "type": activity.get("type"),
        "id": activity.get("id"),
        "start_date": activity.get("start_date"),
        "average_speed": activity.get("average_speed"),
        "max_speed": activity.get("max_speed")
    }

def fetch_activities(access_token, per_page=30, page=1, after=None):
    """
    Fetches activities from Strava API for the authenticated athlete.
    'after' is an epoch timestamp to filter activities.
    """
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {
        "per_page": per_page,
        "page": page
    }
    if after:
        params["after"] = int(after)
    
    activities_url = "https://www.strava.com/api/v3/athlete/activities"
    response = requests.get(activities_url, headers=headers, params=params)
    
    if response.status_code != 200:
        raise Exception(f"Strava API error: {response.text}")
        
    return response.json()

def fetch_recent_activities(access_token, days=7):
    """
    Fetches activities from the last X days and maps them.
    """
    # Calculate epoch for X days ago
    start_date = datetime.datetime.now() - datetime.timedelta(days=days)
    after_timestamp = time.mktime(start_date.timetuple())
    
    # We might need more per_page if many activities are expected
    raw_activities = fetch_activities(access_token, after=after_timestamp, per_page=200)
    return [map_activity(a) for a in raw_activities]
