from googleapiclient.discovery import build
import google.auth


def get_sheets_service():
    """
    Initializes the Google Sheets API service using default credentials.
    In Cloud Functions, this uses the service account.
    Locally, it uses application default credentials.
    """
    credentials, _ = google.auth.default(
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=credentials)


def get_existing_ids(spreadsheet_id, sheet_name="Sheet1"):
    """
    Fetches the 'id' column (assumed to be Column A based on the mapping)
    to prevent duplicates.
    """
    service = get_sheets_service()
    sheet = service.spreadsheets()

    # We'll assume Column A is the ID column (id is the 6th field in our mapping)
    # If the sheet is empty, this might return an error or empty list
    try:
        range_name = f"{sheet_name}!A:A"
        result = (
            sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        )
        values = result.get("values", [])
        # Flatten the list and convert to strings
        return {str(row[0]) for row in values if row}
    except Exception as e:
        print(f"Error fetching existing IDs: {e}")
        return set()


def append_activities(
    spreadsheet_id,
    activities,
    sheet_name="Sheet1",
    column_definition=None,
    column_labels=None,
):
    """
    Appends unique activities to the spreadsheet.
    """
    if not activities:
        return 0

    existing_ids = get_existing_ids(spreadsheet_id, sheet_name)

    # Filter for unique activities
    new_activities = [a for a in activities if str(a["id"]) not in existing_ids]

    if not new_activities:
        print("No new activities to append.")
        return 0

    # Prepare rows for appending
    rows = []
    for a in new_activities:
        if column_definition:
            rows.append([a.get(key) for key in column_definition])
        else:
            rows.append(
                [
                    a["name"],
                    a["distance"],
                    a["moving_time"],
                    a["elapsed_time"],
                    a["type"],
                    str(a["id"]),
                    a["start_date"],
                    a["average_speed"],
                    a["max_speed"],
                ]
            )

    service = get_sheets_service()
    sheet = service.spreadsheets()

    # Check if sheet is empty and write headers if needed
    try:
        range_name = f"{sheet_name}!A1"
        result = (
            sheet.values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        )
        values = result.get("values", [])

        if not values:
            # Sheet is empty, write headers first
            if column_labels:
                headers = [
                    column_labels.get(key, key)
                    for key in column_definition
                    if key in column_definition
                ]
                body = {"values": [headers]}
                sheet.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    body=body,
                ).execute()
                print(f"Headers written to sheet {sheet_name}.")

            # Now append data
            body = {"values": rows}
            result = (
                sheet.values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
        else:
            # Sheet already has data, just append
            body = {"values": rows}
            result = (
                sheet.values()
                .append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption="RAW",
                    insertDataOption="INSERT_ROWS",
                    body=body,
                )
                .execute()
            )
    except Exception as e:
        print(f"Error appending activities: {e}")
        return 0

    updated_rows = result.get("updates", {}).get("updatedRows", 0)
    print(f"Successfully appended {updated_rows} new activities.")
    return updated_rows
