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
    # Use os.path.join for file paths
    token_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "token.pickle")
    credentials_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "credentials.json")

    if os.path.exists(token_path):
        with open(token_path, "rb") as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES, redirect_uri="http://localhost:8080/"
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

        with open(token_path, "wb") as token:
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
        # First: List ALL files in the folder (not just spreadsheets) for debugging
        debug_query = f"'{folder_id}' in parents and trashed=false"
        
        debug_results = (
            drive_service.files()
            .list(
                q=debug_query,
                spaces="drive",
                fields="files(id, name, mimeType)",
                orderBy="modifiedTime desc",
                pageSize=100,
            )
            .execute(num_retries=5)
        )
        
        debug_files = debug_results.get("files", [])
        print(f"🔍 DEBUG - Found {len(debug_files)} total files in folder:")
        for f in debug_files[:10]:  # Show first 10 files
            print(f"  - {f['name']} (Type: {f['mimeType']})")
        if len(debug_files) > 10:
            print(f"  ... and {len(debug_files) - 10} more files")

        # Now search specifically for spreadsheets
        all_files_query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"

        results = (
            drive_service.files()
            .list(
                q=all_files_query,
                spaces="drive",
                fields="files(id, name)",
                orderBy="modifiedTime desc",
                pageSize=100,
            )
            .execute(num_retries=5)
        )

        all_files = results.get("files", [])

        if all_files:
            print(f"ℹ️ Found {len(all_files)} spreadsheets in the folder:")
            for f in all_files:
                print(f"  - {f['name']} (ID: {f['id']})")

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
            if "pubplus_campaign_data" in clean_name or "pubplus" in clean_name:
                for f in all_files:
                    if (
                        "pubplus" in f["name"].lower()
                        and ("campaign" in f["name"].lower() or "data" in f["name"].lower())
                    ):
                        print(
                            f"✅ Found PubPlus campaign data file: {f['name']} (ID: {f['id']})"
                        )
                        return f

            # Fourth try: More flexible matching for any file containing key terms
            search_terms = ["pubplus", "campaign", "data"]
            for f in all_files:
                matches = sum(1 for term in search_terms if term in f["name"].lower())
                if matches >= 2:  # At least 2 of the 3 terms match
                    print(f"✅ Found flexible match ({matches}/3 terms): {f['name']} (ID: {f['id']})")
                    return f

        else:
            print("⚠️ No spreadsheets found in the folder")

        # File not found - provide detailed error message
        error_message = f"❌ Could not find spreadsheet matching '{file_name}' in Google Drive folder"
        print(error_message)
        print("🔍 Please check:")
        print("  1. The spreadsheet exists in the 'campaign_data' folder")
        print("  2. The file name contains 'pubplus' and 'campaign' or 'data'")
        print("  3. The file is a Google Sheets spreadsheet (not CSV or other format)")
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
                .execute(num_retries=5)
            )

            all_files = results.get("files", [])
            if all_files:
                print(f"🔍 Recovery found {len(all_files)} spreadsheets:")
                for f in all_files:
                    print(f"  - {f['name']}")
                    if any(term in f["name"].lower() for term in ["pubplus", "campaign", "data"]):
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


def upload_df_to_drive(drive_service, sheets_service, df, folder_id):
    """Upload DataFrame directly to Google Drive as a spreadsheet, merging with existing data"""
    # Use the specific spreadsheet ID provided by the user
    spreadsheet_id = "1ji8TqRxYScW_OzK0T1Z39WOHkFMrAOqIC6Td46Ojt04"
    
    # Make a copy of the dataframe to avoid modifying the original
    new_data_df = df.copy()
    
    # Convert date column to datetime
    new_data_df['date'] = pd.to_datetime(new_data_df['date'])
    new_data_df = new_data_df.fillna("")  # Replace NaN values
    
    # Get the date range of new data
    min_new_date = new_data_df['date'].min()
    max_new_date = new_data_df['date'].max()
    
    print(f"\n🔍 Debug - New data date range:")
    print(f"  Min date: {min_new_date}")
    print(f"  Max date: {max_new_date}")
    print(f"  Total rows: {len(new_data_df)}")

    print(f"ℹ️ Using specific spreadsheet ID: {spreadsheet_id}")

    try:
        # Get the sheet
        sheet_metadata = sheets_service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        if "sheets" in sheet_metadata and len(sheet_metadata["sheets"]) > 0:
            sheet_title = sheet_metadata["sheets"][0]["properties"]["title"]
            print(f"ℹ️ Found sheet with name: {sheet_title}")
        else:
            error_message = "❌ No sheets found in the spreadsheet"
            print(error_message)
            send_notification_with_fallback(f"ERROR: {error_message}")
            return None

        # Get existing data
        existing_data = sheets_service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_title}"
        ).execute()

        # Get the existing column headers from the sheet first
        existing_headers = None
        if 'values' in existing_data and len(existing_data['values']) > 0:
            existing_headers = existing_data['values'][0]
            print(f"\n🔍 Debug - Existing sheet headers ({len(existing_headers)} columns):")
            print(f"  Headers: {existing_headers}")
        
        print(f"\n🔍 Debug - New data headers ({len(new_data_df.columns)} columns):")
        print(f"  Headers: {list(new_data_df.columns)}")
        
        # Align new data to match existing sheet structure FIRST
        if existing_headers:
            print(f"\n🔍 Debug - Aligning new data to existing sheet structure...")
            new_data_aligned = pd.DataFrame()
            for col in existing_headers:
                if col in new_data_df.columns:
                    new_data_aligned[col] = new_data_df[col]
                else:
                    new_data_aligned[col] = ""  # Fill missing columns with empty strings
                    print(f"  ⚠️ Column '{col}' missing in new data, filling with empty values")
            
            # Check for extra columns in new data that don't exist in sheet
            extra_columns = [col for col in new_data_df.columns if col not in existing_headers]
            if extra_columns:
                print(f"  ⚠️ Extra columns in new data (will be ignored): {extra_columns}")
            
            print(f"\n🔍 Debug - After alignment:")
            print(f"  Existing sheet columns: {len(existing_headers)}")
            print(f"  Aligned new data columns: {len(new_data_aligned.columns)}")
            print(f"  Column match: {list(existing_headers) == list(new_data_aligned.columns)}")
            
            # Use the aligned data
            new_data_df = new_data_aligned
            print(f"  ✅ New data successfully aligned to {len(new_data_df.columns)} columns")

        try:
            print(f"\n🔍 Debug - Starting data processing...")
            print(f"  New data columns before processing: {len(new_data_df.columns)}")
            
            if 'values' in existing_data and len(existing_data['values']) > 1:
                # Debug the raw data structure from Google Sheets
                print(f"\n🔍 Debug - Raw Google Sheets data structure:")
                print(f"  Total rows in existing_data: {len(existing_data['values'])}")
                print(f"  Header row length: {len(existing_data['values'][0])}")
                
                # Check the length of the first few data rows
                for i in range(1, min(6, len(existing_data['values']))):
                    row_length = len(existing_data['values'][i])
                    print(f"  Row {i} length: {row_length}")
                    if row_length != len(existing_data['values'][0]):
                        print(f"    ⚠️ Row {i} has different length than header!")
                        print(f"    Header: {len(existing_data['values'][0])} columns")
                        print(f"    Row {i}: {row_length} columns")
                        # Show the extra data
                        if row_length > len(existing_data['values'][0]):
                            extra_data = existing_data['values'][i][len(existing_data['values'][0]):]
                            print(f"    Extra data in row {i}: {extra_data}")
                
                # Try to create DataFrame with error handling
                try:
                    existing_df = pd.DataFrame(existing_data['values'][1:], columns=existing_headers)
                    print(f"  ✅ Successfully created existing_df with {len(existing_df.columns)} columns")
                except Exception as df_error:
                    print(f"  ❌ Error creating DataFrame: {df_error}")
                    
                    # Try to fix by truncating rows to match header length
                    print(f"  🔧 Attempting to fix by truncating rows to header length...")
                    fixed_data = []
                    header_length = len(existing_headers)
                    
                    for row in existing_data['values'][1:]:
                        if len(row) > header_length:
                            fixed_row = row[:header_length]  # Truncate to header length
                            fixed_data.append(fixed_row)
                        elif len(row) < header_length:
                            # Pad with empty strings if row is shorter
                            fixed_row = row + [''] * (header_length - len(row))
                            fixed_data.append(fixed_row)
                        else:
                            fixed_data.append(row)
                    
                    existing_df = pd.DataFrame(fixed_data, columns=existing_headers)
                    print(f"  ✅ Fixed and created existing_df with {len(existing_df.columns)} columns")
                
                print(f"  Created existing_df with {len(existing_df.columns)} columns")
                
                existing_df['date'] = pd.to_datetime(existing_df['date'])
                print(f"  After date conversion, existing_df has {len(existing_df.columns)} columns")
                
                print(f"\n🔍 Debug - Existing sheet data:")
                print(f"  Total existing rows: {len(existing_df)}")
                print(f"  Existing date range: {existing_df['date'].min()} to {existing_df['date'].max()}")
                print(f"  Existing data columns: {len(existing_df.columns)}")

                # Remove ALL existing data that falls within the new data date range
                # This prevents duplication when re-running for the same dates
                old_data_df = existing_df[
                    (existing_df['date'] < min_new_date) | 
                    (existing_df['date'] > max_new_date)
                ]
                print(f"  After filtering, old_data_df has {len(old_data_df.columns)} columns")
                
                # Count how many rows we're removing
                removed_rows = len(existing_df) - len(old_data_df)
                
                print(f"\n🔍 Debug - Data filtering:")
                print(f"  Rows being removed (overlapping dates): {removed_rows}")
                print(f"  Rows kept from existing data: {len(old_data_df)}")
                print(f"  Old data columns: {len(old_data_df.columns)}")
                print(f"  New data columns before concat: {len(new_data_df.columns)}")
                if len(old_data_df) > 0:
                    print(f"  Kept data date range: {old_data_df['date'].min()} to {old_data_df['date'].max()}")
                
                # Ensure both dataframes have exactly the same columns before concatenation
                if len(old_data_df.columns) != len(new_data_df.columns):
                    print(f"  ⚠️ Column mismatch before concat: old={len(old_data_df.columns)}, new={len(new_data_df.columns)}")
                    # Force both to have the same columns as existing headers
                    old_data_df = old_data_df.reindex(columns=existing_headers, fill_value="")
                    new_data_df = new_data_df.reindex(columns=existing_headers, fill_value="")
                    print(f"  ✅ Forced both to {len(existing_headers)} columns")
                    print(f"  After reindex - old_data_df: {len(old_data_df.columns)}, new_data_df: {len(new_data_df.columns)}")
                
                # Combine old and new data
                print(f"  About to concat - old_data_df: {len(old_data_df.columns)}, new_data_df: {len(new_data_df.columns)}")
                combined_df = pd.concat([old_data_df, new_data_df], ignore_index=True)
                print(f"  Combined data columns after concat: {len(combined_df.columns)}")
                
            else:
                # No existing data, just use new data
                print(f"\n🔍 Debug - No existing data found, using new data only")
                combined_df = new_data_df.copy()
                print(f"  Combined data columns (new only): {len(combined_df.columns)}")
            
            # Sort by date in descending order (newest first)
            print(f"  Before sorting: {len(combined_df.columns)} columns")
            combined_df = combined_df.sort_values('date', ascending=False)
            print(f"  After sorting: {len(combined_df.columns)} columns")
            
            print(f"\n🔍 Debug - Final combined data:")
            print(f"  Total rows: {len(combined_df)}")
            print(f"  Date range: {combined_df['date'].min()} to {combined_df['date'].max()}")
            print(f"  Columns after sorting: {len(combined_df.columns)}")
            
            # Convert back to string format for upload
            print(f"  Before date string conversion: {len(combined_df.columns)} columns")
            combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
            print(f"  Columns after date conversion: {len(combined_df.columns)}")
            
        except Exception as e:
            print(f"❌ Error in data processing section: {e}")
            print(f"  Current new_data_df columns: {len(new_data_df.columns)}")
            if 'existing_df' in locals():
                print(f"  Current existing_df columns: {len(existing_df.columns)}")
            if 'combined_df' in locals():
                print(f"  Current combined_df columns: {len(combined_df.columns)}")
            raise e
        
        # Final verification - ensure column count matches exactly
        if existing_headers:
            expected_columns = len(existing_headers)
            actual_columns = len(combined_df.columns)
            
            print(f"\n🔍 Debug - Final column verification:")
            print(f"  Expected columns (from sheet): {expected_columns}")
            print(f"  Actual columns (combined data): {actual_columns}")
            
            if expected_columns != actual_columns:
                print(f"  ❌ Column count mismatch detected!")
                print(f"  Expected headers: {existing_headers}")
                print(f"  Actual headers: {list(combined_df.columns)}")
                
                # Force alignment to existing sheet structure
                aligned_df = pd.DataFrame()
                for col in existing_headers:
                    if col in combined_df.columns:
                        aligned_df[col] = combined_df[col]
                    else:
                        aligned_df[col] = ""
                        print(f"    Adding missing column '{col}' with empty values")
                
                combined_df = aligned_df
                print(f"  ✅ Forced alignment complete. New column count: {len(combined_df.columns)}")
            else:
                print(f"  ✅ Column count matches perfectly!")
        
        # Clear the entire sheet and upload all data
        sheets_service.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=f"{sheet_title}"
        ).execute()
        print(f"ℹ️ Cleared sheet for complete update")
        
        # Prepare data for upload in chunks
        chunk_size = 1000
        
        # Upload header first - use existing headers to maintain consistency
        if existing_headers:
            header_values = [existing_headers]
        else:
            header_values = [combined_df.columns.tolist()]
            
        print(f"ℹ️ About to upload headers: {len(header_values[0])} columns")
        print(f"ℹ️ Combined data has: {len(combined_df.columns)} columns")
        
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_title}!A1",
            valueInputOption="RAW",
            body={"values": header_values},
        ).execute()
        
        print(f"ℹ️ Uploaded headers: {len(header_values[0])} columns")
        
        # Upload data in chunks
        for i in range(0, len(combined_df), chunk_size):
            chunk = combined_df.iloc[i:i+chunk_size]
            chunk_values = []
            for _, row in chunk.iterrows():
                row_values = [str(val) if val != "" else "" for val in row.tolist()]
                if len(row_values) != len(header_values[0]):
                    print(f"  ⚠️ Row {i} has {len(row_values)} values but header has {len(header_values[0])} columns")
                    # Pad or trim to match header length
                    while len(row_values) < len(header_values[0]):
                        row_values.append("")
                    row_values = row_values[:len(header_values[0])]
                chunk_values.append(row_values)
            
            # Calculate the starting row (A2 for first chunk, then continue)
            start_row = i + 2  # +2 because row 1 is header and we're 0-indexed
            range_name = f"{sheet_title}!A{start_row}"
            
            sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="RAW",
                body={"values": chunk_values},
            ).execute()
            
            print(f"✅ Uploaded chunk {i//chunk_size + 1} of {(len(combined_df) + chunk_size - 1)//chunk_size}")
            time.sleep(0.5)  # Small delay between chunks

        print(f"✅ Successfully updated spreadsheet with {len(combined_df)} total rows")
        return spreadsheet_id

    except Exception as e:
        error_message = f"❌ Error updating spreadsheet: {e}"
        print(error_message)
        send_notification_with_fallback(f"ERROR: {error_message}")
        return None


def list_drive_folder_contents(drive_service, folder_id):
    """List all contents of a Google Drive folder for debugging"""
    try:
        print(f"\n🔍 DEBUGGING - Listing all contents of folder ID: {folder_id}")
        
        # Get all files in the folder
        query = f"'{folder_id}' in parents and trashed=false"
        
        results = (
            drive_service.files()
            .list(
                q=query,
                spaces="drive",
                fields="files(id, name, mimeType, modifiedTime, size)",
                orderBy="modifiedTime desc",
                pageSize=100,
            )
            .execute(num_retries=5)
        )
        
        all_files = results.get("files", [])
        
        if all_files:
            print(f"📁 Found {len(all_files)} files in the folder:")
            print("-" * 80)
            
            spreadsheets = []
            other_files = []
            
            for f in all_files:
                file_info = {
                    'name': f['name'],
                    'id': f['id'],
                    'type': f['mimeType'],
                    'modified': f.get('modifiedTime', 'Unknown'),
                    'size': f.get('size', 'N/A')
                }
                
                if f['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                    spreadsheets.append(file_info)
                else:
                    other_files.append(file_info)
            
            # Show spreadsheets first
            if spreadsheets:
                print(f"📊 SPREADSHEETS ({len(spreadsheets)}):")
                for f in spreadsheets:
                    print(f"  ✅ {f['name']}")
                    print(f"     ID: {f['id']}")
                    print(f"     Modified: {f['modified']}")
                    print()
            
            # Show other files
            if other_files:
                print(f"📄 OTHER FILES ({len(other_files)}):")
                for f in other_files:
                    file_type = f['type'].split('/')[-1] if '/' in f['type'] else f['type']
                    print(f"  📄 {f['name']} ({file_type})")
                    print(f"     ID: {f['id']}")
                    print(f"     Modified: {f['modified']}")
                    if f['size'] != 'N/A':
                        print(f"     Size: {f['size']} bytes")
                    print()
            
            print("-" * 80)
            
            # Look for potential matches
            potential_matches = []
            search_terms = ["pubplus", "campaign", "data"]
            
            for f in spreadsheets:
                matches = sum(1 for term in search_terms if term.lower() in f['name'].lower())
                if matches > 0:
                    potential_matches.append((f, matches))
            
            if potential_matches:
                print("🎯 POTENTIAL MATCHES FOR PUBPLUS DATA:")
                for f, match_count in sorted(potential_matches, key=lambda x: x[1], reverse=True):
                    print(f"  🎯 {f['name']} ({match_count}/3 terms matched)")
                    print(f"     ID: {f['id']}")
                    print()
            else:
                print("⚠️ No spreadsheets found that match 'pubplus', 'campaign', or 'data'")
                
        else:
            print("📁 The folder is empty or no files found")
            
    except Exception as e:
        print(f"❌ Error listing folder contents: {e}")
