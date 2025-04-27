from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import os
import pickle
import pandas as pd
import time

# Update scopes to include both Drive and Sheets APIs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def get_google_drive_service():
    """Gets authenticated Drive and Sheets services"""
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES, redirect_uri="http://localhost:8080/"
                )
                creds = flow.run_local_server(
                    port=8080,
                    success_message="Authentication successful! You can close this window.",
                    open_browser=True,
                )
            except Exception as e:
                print(f"Authentication error: {e}")
                print(
                    "Please make sure you've added http://localhost:8080/ to your OAuth 2.0 Client authorized redirect URIs"
                )
                raise

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    drive_service = build("drive", "v3", credentials=creds)

    # Add retry logic for Sheets API
    sheets_service = None
    max_retries = 3
    retry_delay = 20  # seconds

    for attempt in range(max_retries):
        try:
            sheets_service = build("sheets", "v4", credentials=creds)
            # Test the service with a simple call
            sheets_service.spreadsheets().get(spreadsheetId="dummy").execute()
            break
        except HttpError as e:
            if "SERVICE_DISABLED" in str(e):
                if attempt < max_retries - 1:
                    print(
                        f"\nWARNING: Google Sheets API not ready (attempt {attempt + 1}/{max_retries})"
                    )
                    print("If you just enabled the API, please wait...")
                    print(f"Retrying in {retry_delay} seconds...\n")
                    time.sleep(retry_delay)
                    continue
                print("\nERROR: Google Sheets API is not enabled!")
                print("Please follow these steps:")
                print(
                    "1. Go to: https://console.developers.google.com/apis/api/sheets.googleapis.com"
                )
                print("2. Click 'Enable API'")
                print("3. Wait a few minutes for the changes to take effect")
                print("4. Run this script again\n")
            elif "404" in str(e) and "Requested entity was not found" in str(e):
                # This is expected - the API is working but the 'dummy' spreadsheet doesn't exist
                # Consider the API to be working correctly and continue
                break
            else:
                print(f"Warning: Sheets API initialization failed: {e}")
        except Exception as e:
            print(f"Warning: Unexpected error with Sheets API: {e}")
            break

    return drive_service, sheets_service


def create_folder_if_not_exists(service, folder_name, parent_id=None):
    """Creates a folder in Google Drive if it doesn't exist already"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    if parent_id:
        query += f" and '{parent_id}' in parents"

    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )

    items = results.get("files", [])

    if not items:
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        if parent_id:
            file_metadata["parents"] = [parent_id]

        folder = service.files().create(body=file_metadata, fields="id, name").execute()
        print(f"Created new folder: {folder['name']} (ID: {folder['id']})")
        return folder.get("id")

    print(f"Found existing folder: {items[0]['name']} (ID: {items[0]['id']})")
    return items[0]["id"]


def find_spreadsheet(drive_service, file_name, folder_id):
    """Find existing spreadsheet by name in a specific folder with improved robustness"""
    # Normalize the file name - remove .csv extension and trim spaces
    original_file_name = file_name
    file_name = file_name.replace(".csv", "").strip()

    print(f"Searching for file named '{file_name}' in folder ID: {folder_id}")

    try:
        # First try: Exact match (case-sensitive)
        exact_query = f"name='{file_name}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

        results = (
            drive_service.files()
            .list(
                q=exact_query,
                spaces="drive",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])

        if files:
            print(
                f"Found existing spreadsheet: {files[0]['name']} (ID: {files[0]['id']})"
            )
            return files[0]

        # Second try: Case-insensitive search
        print(f"No exact match found. Trying case-insensitive search...")
        case_insensitive_query = f"name contains '{file_name}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

        results = (
            drive_service.files()
            .list(
                q=case_insensitive_query,
                spaces="drive",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        files = results.get("files", [])

        # Filter for exact name (case-insensitive)
        exact_matches = [f for f in files if f["name"].lower() == file_name.lower()]
        if exact_matches:
            print(
                f"Found case-insensitive match: {exact_matches[0]['name']} (ID: {exact_matches[0]['id']})"
            )
            return exact_matches[0]

        # Third try: List all spreadsheets in the folder for debugging and potential matches
        print(f"No case-insensitive match. Retrieving all spreadsheets in folder...")
        all_files_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

        results = (
            drive_service.files()
            .list(
                q=all_files_query,
                spaces="drive",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )

        all_files = results.get("files", [])

        if all_files:
            print(f"Found {len(all_files)} spreadsheets in the folder:")
            for f in all_files:
                print(f"  - {f['name']} (ID: {f['id']})")

            # Look for files with similar names (partial matches)
            for f in all_files:
                # Check if our filename is in the spreadsheet name or vice versa
                if (
                    file_name.lower() in f["name"].lower()
                    or f["name"].lower() in file_name.lower()
                    or
                    # Also check with original filename (with .csv)
                    original_file_name.lower() in f["name"].lower()
                ):
                    print(f"Found similar match: {f['name']} (ID: {f['id']})")
                    return f

        print(f"No existing spreadsheet found with name '{file_name}'")
        return None

    except Exception as e:
        print(f"Error searching for spreadsheet: {e}")
        # Attempt a basic recovery with a simpler query
        try:
            print("Attempting recovery with basic folder query...")
            basic_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

            results = (
                drive_service.files()
                .list(q=basic_query, spaces="drive", fields="files(id, name)")
                .execute()
            )

            all_files = results.get("files", [])
            if all_files:
                for f in all_files:
                    if file_name.lower() in f["name"].lower():
                        print(f"Recovery found potential match: {f['name']}")
                        return f
        except Exception as recovery_error:
            print(f"Recovery attempt failed: {recovery_error}")

        return None


def upload_csv_to_drive(drive_service, sheets_service, file_path, folder_id):
    """Upload CSV data to Google Drive as a spreadsheet, updating if exists"""
    file_name = os.path.basename(file_path)

    # If Sheets API is not available, fall back to simple file replacement
    if not sheets_service:
        print(
            "\nFalling back to simple file replacement since Sheets API is not available"
        )
        print(
            "Note: This will not preserve any formatting or formulas in existing sheets"
        )
        existing_file = find_spreadsheet(drive_service, file_name, folder_id)

        if existing_file:
            try:
                drive_service.files().delete(fileId=existing_file["id"]).execute()
                print(f"Deleted existing file: {existing_file['name']}")
            except Exception as e:
                print(f"Warning: Could not delete existing file: {e}")

        # Create new file
        media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)
        file_metadata = {
            "name": file_name,
            "parents": [folder_id],
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        try:
            file = (
                drive_service.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                    fields="id, name",
                    supportsAllDrives=True,
                )
                .execute()
            )
            print(
                f"Successfully created new spreadsheet: {file['name']} (ID: {file['id']})"
            )
            return file["id"]
        except Exception as e:
            print(f"Error creating new spreadsheet: {e}")
            raise

    # Load new CSV data and clean NaN values
    new_data_df = pd.read_csv(file_path)
    # Replace NaN values with empty string for JSON compatibility
    new_data_df = new_data_df.fillna("")
    print(f"Loaded {len(new_data_df)} rows of new data from {file_path}")

    # First, attempt to find the existing file
    existing_file = find_spreadsheet(drive_service, file_name, folder_id)

    if existing_file:
        try:
            spreadsheet_id = existing_file["id"]
            print(f"Working with existing spreadsheet ID: {spreadsheet_id}")

            # Get existing data from the sheet
            sheet_metadata = (
                sheets_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
            )
            sheet_title = sheet_metadata["sheets"][0]["properties"]["title"]
            print(f"Reading data from sheet: {sheet_title}")

            sheet_data = (
                sheets_service.spreadsheets()
                .values()
                .get(spreadsheetId=spreadsheet_id, range=sheet_title)
                .execute()
            )

            if "values" in sheet_data and len(sheet_data["values"]) > 1:
                print(f"Found {len(sheet_data['values']) - 1} rows of existing data")

                # Convert Google Sheet data to DataFrame
                existing_headers = sheet_data["values"][0]
                existing_data = sheet_data["values"][1:]

                # Handle empty cells in the data
                for row in existing_data:
                    while len(row) < len(existing_headers):
                        row.append("")

                existing_df = pd.DataFrame(existing_data, columns=existing_headers)

                # Convert date strings to datetime for comparison
                if "date" in existing_df.columns and "date" in new_data_df.columns:
                    existing_df["date"] = pd.to_datetime(
                        existing_df["date"], errors="coerce"
                    )
                    new_data_df["date"] = pd.to_datetime(
                        new_data_df["date"], errors="coerce"
                    )

                # Create unique keys for identifying unique rows
                if (
                    "campaign_id" in existing_df.columns
                    and "campaign_id" in new_data_df.columns
                ):
                    existing_df["unique_key"] = (
                        existing_df["date"].astype(str)
                        + "_"
                        + existing_df["campaign_id"].astype(str)
                    )
                    new_data_df["unique_key"] = (
                        new_data_df["date"].astype(str)
                        + "_"
                        + new_data_df["campaign_id"].astype(str)
                    )

                    # Remove rows from existing data that will be updated
                    merged_df = pd.concat(
                        [
                            existing_df[
                                ~existing_df["unique_key"].isin(
                                    new_data_df["unique_key"]
                                )
                            ],
                            new_data_df,
                        ]
                    )
                    merged_df = merged_df.drop(columns=["unique_key"])

                    # Convert dates back to string format
                    if "date" in merged_df.columns:
                        merged_df["date"] = merged_df["date"].dt.strftime("%Y-%m-%d")

                    print(f"Merged data has {len(merged_df)} rows")

                    # Sort by date and campaign_id
                    if (
                        "date" in merged_df.columns
                        and "campaign_id" in merged_df.columns
                    ):
                        merged_df = merged_df.sort_values(["date", "campaign_id"])

                    # Prepare data for uploading - ensure all values are JSON-safe
                    values = [merged_df.columns.tolist()]
                    for _, row in merged_df.iterrows():
                        # Convert each value to string if not empty
                        cleaned_row = [
                            str(val) if val != "" else "" for val in row.tolist()
                        ]
                        values.append(cleaned_row)

                    # Clear the sheet first
                    clear_request = (
                        sheets_service.spreadsheets()
                        .values()
                        .clear(spreadsheetId=spreadsheet_id, range=sheet_title)
                    )
                    clear_request.execute()
                    print(f"Cleared existing data from sheet")

                    # Then update with new data
                    update_request = (
                        sheets_service.spreadsheets()
                        .values()
                        .update(
                            spreadsheetId=spreadsheet_id,
                            range=f"{sheet_title}!A1",
                            valueInputOption="RAW",
                            body={"values": values},
                        )
                    )
                    response = update_request.execute()
                    print(
                        f"Updated {response.get('updatedCells')} cells in the spreadsheet"
                    )

                    return spreadsheet_id
                else:
                    print("Missing required columns to identify unique rows")
            else:
                print("No values found in existing sheet or header only")
        except Exception as e:
            print(f"Error updating existing spreadsheet: {e}")
            print("Falling back to file replacement method")

    # If we couldn't update or no file exists, create a new file
    print("Creating new spreadsheet...")
    media = MediaFileUpload(file_path, mimetype="text/csv", resumable=True)
    file_metadata = {
        "name": file_name,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.spreadsheet",
    }

    file = (
        drive_service.files()
        .create(
            body=file_metadata,
            media_body=media,
            fields="id, name",
            supportsAllDrives=True,
        )
        .execute()
    )

    print(f"Created new spreadsheet: {file['name']} (ID: {file['id']})")
    return file["id"]

    # Last Commit | Working
