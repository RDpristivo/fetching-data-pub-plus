from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    SCOPES,
                    redirect_uri='http://localhost:8080/'
                )
                creds = flow.run_local_server(
                    port=8080,
                    success_message='Authentication successful! You can close this window.',
                    open_browser=True
                )
            except Exception as e:
                print(f"Authentication error: {e}")
                print("Please make sure you've added http://localhost:8080/ to your OAuth 2.0 Client authorized redirect URIs")
                raise

        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)

def create_folder_if_not_exists(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    
    results = service.files().list(q=query, spaces='drive').execute()
    items = results.get('files', [])

    if not items:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    
    return items[0]['id']

def find_file_in_folder(service, file_name, folder_id):
    """Search for a file by name in a specific folder."""
    query = f"name='{file_name}' and '{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
    results = service.files().list(
        q=query,
        spaces='drive',
        fields='files(id, name)'
    ).execute()
    files = results.get('files', [])
    return files[0] if files else None

def upload_csv_to_drive(service, file_path, folder_id):
    file_name = os.path.basename(file_path)
    
    # Search for existing file
    existing_file = find_file_in_folder(service, file_name, folder_id)
    print(f"Existing file found: {existing_file}") if existing_file else print("No existing file found.")
    media = MediaFileUpload(file_path, mimetype='text/csv', resumable=True)
    
    if existing_file:
        # Update existing file's content only
        try:
            file = service.files().update(
                fileId=existing_file['id'],
                media_body=media,
                fields='id',
                supportsAllDrives=True
            ).execute()
            print(f"Successfully updated existing spreadsheet with ID: {file['id']}")
            return file['id']
        except Exception as e:
            print(f"Error updating file: {e}")
            raise
    else:
        # First time creation only
        file_metadata = {
            'name': file_name,
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()
        print(f"First time creation of spreadsheet with ID: {file['id']}")
        return file['id']
