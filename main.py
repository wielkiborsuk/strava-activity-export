import json
import functions_framework
import strava
import config

@functions_framework.http
def extract_strava_activities(request):
    """
    HTTP Cloud Function entry point.
    """
    try:
        # 1. Gather Secrets
        client_id = config.get_secret("STRAVA_CLIENT_ID")
        client_secret = config.get_secret("STRAVA_CLIENT_SECRET")
        refresh_token = config.get_secret("STRAVA_REFRESH_TOKEN")

        # 2. Get Access Token
        access_token = strava.get_access_token(
            client_id, 
            client_secret, 
            refresh_token, 
            on_token_refresh=lambda new_token: config.update_secret("STRAVA_REFRESH_TOKEN", new_token)
        )
        
        # 3. Extract Request Parameters
        try:
            days = int(request.args.get("days", 7))
        except ValueError:
            days = 7
        
        # 4. Fetch Recent Activities (Mapped)
        print(f"Fetching activities from the last {days} days...")
        activities = strava.fetch_recent_activities(access_token, days=days)
        
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
