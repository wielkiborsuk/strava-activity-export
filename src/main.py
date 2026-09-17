import json
import functions_framework
from strava.browser_automation import BrowserAutomation
from strava.strava_browser import StravaBrowser
from config import get_secret
from google.spreadsheet import append_activities


@functions_framework.http
def extract_strava_activities(request):
    """
    HTTP Cloud Function entry point.
    """
    try:
        # 1. Gather Secrets
        user = request.args.get("user", "michal")

        # Get Spreadsheet ID (can be in secret or passed in request)
        spreadsheet_id = get_secret("STRAVA_SPREADSHEET_ID")
        sheet_name = user.capitalize()

        activities = []

        # 5. Append to Spreadsheet (Ensuring unique IDs)
        print(
            f"Appending activities to spreadsheet {spreadsheet_id} in sheet {sheet_name}..."
        )

        # Column definition for ordering and labels
        column_definition = [
            "id",
            "start_date",
            "type",
            "name",
            "distance",
            "moving_time",
            "elapsed_time",
            "average_speed",
            "max_speed",
        ]
        column_labels = {
            "id": "ID",
            "start_date": "Date",
            "type": "Activity Type",
            "name": "Activity Name",
            "distance": "Distance (m)",
            "moving_time": "Moving Time (s)",
            "elapsed_time": "Elapsed Time (s)",
            "average_speed": "Avg Speed (m/s)",
            "max_speed": "Max Speed (m/s)",
        }

        updated_rows = append_activities(
            spreadsheet_id,
            activities,
            sheet_name=sheet_name,
            column_definition=column_definition,
            column_labels=column_labels,
        )

        result = {
            "status": "success",
            "activities_fetched": len(activities),
            "new_activities_added": updated_rows,
            "spreadsheet_id": spreadsheet_id,
        }

        return (json.dumps(result), 200, {"Content-Type": "application/json"})

    except Exception as e:
        print(f"Unhandled exception: {e}")
        return (
            json.dumps({"error": str(e)}),
            500,
            {"Content-Type": "application/json"},
        )
