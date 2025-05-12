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
import threading
import subprocess
import platform
from dotenv import load_dotenv
from twilio_utils import send_notification_with_fallback

# Load environment variables
load_dotenv()

# Update scopes to include both Drive and Sheets APIs
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

# Increased timeout values
SOCKET_TIMEOUT = 120  # seconds
API_TIMEOUT = 300  # seconds


def close_browser_tab():
    """Function to close the browser tab after authentication"""

    def _close_tab():
        # Wait for authentication to complete
        time.sleep(10)

        # For Windows
        if platform.system() == "Windows":
            try:
                subprocess.run(["taskkill", "/F", "/IM", "chrome.exe"], check=False)
                print("Closed Chrome browser on Windows")
            except Exception as e:
                print(f"Failed to close Chrome on Windows: {e}")

        # For macOS
        elif platform.system() == "Darwin":
            try:
                os.system('pkill -a "Google Chrome"')
                print("Closed Chrome browser on macOS")
            except Exception as e:
                print(f"Failed to close Chrome on macOS: {e}")

    # Start thread to close browser
    thread = threading.Thread(target=_close_tab)
    thread.daemon = True
    thread.start()


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

                # Start the thread to close the browser tab
                close_browser_tab()

                creds = flow.run_local_server(
                    port=8080,
                    success_message="Authentication successful! You can close this window.",
                    open_browser=True,
                    timeout_seconds=180,  # Increase timeout for slow VMs
                )
            except Exception as e:
                error_message = f"Authentication error: {e}"
                print(error_message)
                print(
                    "Please make sure you've added http://localhost:8080/ to your OAuth 2.0 Client authorized redirect URIs"
                )
                send_notification_with_fallback(f"ERROR: {error_message}")
                raise

        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    # Add retry logic for Sheets API
    sheets_service = None
    max_retries = 3
    retry_delay = 20  # seconds

    for attempt in range(max_retries):
        try:
            sheets_service = build("sheets", "v4", credentials=creds)
            # Test the service with a simple call
            try:
                sheets_service.spreadsheets().get(spreadsheetId="dummy").execute()
            except:
                # Expected to fail with 404, but confirms API is working
                pass
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
                send_notification_with_fallback(
                    "ERROR: Google Sheets API is not enabled!"
                )
            break
        except Exception as e:
            print(f"Warning: Unexpected error with Sheets API: {e}")
            break

    drive_service = build("drive", "v3", credentials=creds)
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
    print(f"ℹ️ Searching for file '{file_name}' in Google Drive folder")

    try:
        # First: List ALL spreadsheets in the folder with increased timeouts
        all_files_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

        results = (
            drive_service.files()
            .list(
                q=all_files_query,
                spaces="drive",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
                pageSize=100,  # Increase page size to get more results
            )
            .execute(num_retries=5)  # Add retries for reliability
        )

        all_files = results.get("files", [])

        if all_files:
            print(f"ℹ️ Found {len(all_files)} spreadsheets in the folder")

            # First try: Look for exact filename match
            for f in all_files:
                if f["name"].lower() == file_name.lower():
                    print(f"✅ Found exact match: {f['name']} (ID: {f['id']})")
                    return f

            # Second try: Look for filename without .csv extension
            clean_name = file_name.lower()
            for f in all_files:
                clean_file = f["name"].lower().replace(".csv", "").strip()
                if clean_file == clean_name:
                    print(f"✅ Found match after cleaning: {f['name']} (ID: {f['id']})")
                    return f

            # Third try: Check if file name contains our search term or vice versa
            for f in all_files:
                if (
                    clean_name in f["name"].lower()
                    or f["name"].lower() in clean_name
                    or original_file_name.lower() in f["name"].lower()
                ):
                    print(f"✅ Found partial match: {f['name']} (ID: {f['id']})")
                    return f

            # Special case for "pubplus_campaign_data"
            if "pubplus_campaign_data" in clean_name:
                for f in all_files:
                    if (
                        "pubplus" in f["name"].lower()
                        and "campaign" in f["name"].lower()
                    ):
                        print(
                            f"✅ Found PubPlus campaign data file: {f['name']} (ID: {f['id']})"
                        )
                        return f

        # File not found - send notification and return None
        error_message = f"❌ PubPlus data file not found in Google Drive: '{file_name}'"
        print(error_message)
        send_notification_with_fallback(f"ALERT: {error_message}")
        return None

    except Exception as e:
        print(f"❌ Error searching for spreadsheet: {e}")
        # Attempt a basic recovery with a simpler query
        try:
            print("ℹ️ Attempting recovery with basic folder query...")
            basic_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

            results = (
                drive_service.files()
                .list(
                    q=basic_query,
                    spaces="drive",
                    fields="files(id, name)",
                    pageSize=100,
                )
                .execute(num_retries=5)  # More retries for recovery
            )

            all_files = results.get("files", [])
            if all_files:
                for f in all_files:
                    if file_name.lower() in f["name"].lower():
                        print(f"✅ Recovery found potential match: {f['name']}")
                        return f

            # If we reach here, recovery failed as well
            error_message = f"❌ PubPlus data file not found in Google Drive (after recovery attempt)"
            print(error_message)
            send_notification_with_fallback(f"ALERT: {error_message}")

        except Exception as recovery_error:
            error_message = f"❌ Failed to find PubPlus data file: {recovery_error}"
            print(error_message)
            send_notification_with_fallback(f"ALERT: {error_message}")

        return None


def upload_csv_to_drive(drive_service, sheets_service, file_path, folder_id):
    """Upload CSV data to Google Drive as a spreadsheet, updating if exists"""
    file_name = os.path.basename(file_path)

    # Load CSV data
    new_data_df = pd.read_csv(file_path)
    new_data_df = new_data_df.fillna("")  # Replace NaN values
    print(f"ℹ️ Loaded {len(new_data_df)} rows of data from {file_path}")

    # Use the robust find_spreadsheet function to search for existing file
    existing_file = find_spreadsheet(drive_service, file_name, folder_id)

    if existing_file:
        # Update existing spreadsheet
        spreadsheet_id = existing_file["id"]
        print(f"ℹ️ Updating existing spreadsheet: {existing_file['name']}")

        try:
            # Get the actual sheet name from the spreadsheet
            sheet_metadata = (
                sheets_service.spreadsheets()
                .get(spreadsheetId=spreadsheet_id)
                .execute()
            )
            if "sheets" in sheet_metadata and len(sheet_metadata["sheets"]) > 0:
                sheet_title = sheet_metadata["sheets"][0]["properties"]["title"]
                print(f"ℹ️ Found sheet with name: {sheet_title}")
            else:
                # If no sheets found, create a new one named "Data"
                sheet_title = "Data"
                body = {
                    "requests": [{"addSheet": {"properties": {"title": sheet_title}}}]
                }
                sheets_service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id, body=body
                ).execute()
                print(f"ℹ️ Created new sheet with name: {sheet_title}")

            # Prepare data for upload
            values = [new_data_df.columns.tolist()]
            for _, row in new_data_df.iterrows():
                values.append([str(val) if val != "" else "" for val in row.tolist()])

            # Clear existing data
            try:
                sheets_service.spreadsheets().values().clear(
                    spreadsheetId=spreadsheet_id, range=f"{sheet_title}"
                ).execute()
                print(f"ℹ️ Cleared existing data from sheet '{sheet_title}'")
            except Exception as e:
                print(f"⚠️ Could not clear sheet: {e}")
                print("ℹ️ Will attempt to overwrite data instead")

            # Update with new data
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_title}!A1",
                valueInputOption="RAW",
                body={"values": values},
            ).execute()

            print(f"✅ Successfully updated spreadsheet with {len(new_data_df)} rows")
            return spreadsheet_id

        except Exception as e:
            error_message = f"❌ Error updating spreadsheet: {e}"
            print(error_message)
            send_notification_with_fallback(f"ERROR: {error_message}")
            return None

    else:
        # File not found - send notification and return None
        error_message = (
            f"❌ PubPlus data file not found in Google Drive. Cannot update data."
        )
        print(error_message)
        send_notification_with_fallback(f"ALERT: {error_message}")
        return None
