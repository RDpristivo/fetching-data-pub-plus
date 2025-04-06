from datetime import datetime, timedelta
import time
import os
import pandas as pd
from get import get_campaign_data
from csv_handler import process_campaigns_data, save_to_csv
from drive_handler import get_google_drive_service, create_folder_if_not_exists, upload_csv_to_drive

def main():
    print("Starting campaign data collection...")
    
    # Initialize Google Drive and Sheets services
    drive_service, sheets_service = get_google_drive_service()
    
    # Create or get the main campaign_data folder in Google Drive
    drive_folder_id = create_folder_if_not_exists(drive_service, 'campaign_data')
    
    # Create directory for data if it doesn't exist
    output_dir = 'campaign_data'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define the single CSV file path
    filename = os.path.join(output_dir, 'pubplus_campaign_data.csv')
    
    # Get current date and calculate start date (30 days ago)
    today = datetime.now()
    start_date = today - timedelta(days=29)
    
    all_campaigns = []
    
    # Fetch data for each day in the last 30 days
    current_date = start_date
    while current_date <= today:
        date_str = current_date.strftime('%Y-%m-%d')
        start_datetime = f"{date_str} 00:00:00"
        end_datetime = f"{date_str} 23:59:59"
        
        print(f"Fetching data for {date_str}...")
        
        response_data = get_campaign_data(start_datetime, end_datetime)
        
        if response_data:
            campaigns_list = process_campaigns_data(response_data)
            if campaigns_list:
                for campaign in campaigns_list:
                    campaign['date'] = date_str
                all_campaigns.extend(campaigns_list)
        
        current_date += timedelta(days=1)
        time.sleep(1)  # Add delay between requests
    
    if all_campaigns:
        # Save/update local CSV
        save_to_csv(all_campaigns, filename)
        
        # Upload to Google Drive
        try:
            print(f"Uploading data to Google Drive...")
            file_id = upload_csv_to_drive(drive_service, sheets_service, filename, drive_folder_id)
            print(f"Data successfully updated in Google Drive spreadsheet with ID: {file_id}")
        except Exception as e:
            print(f"Error uploading to Google Drive: {e}")
    else:
        print("No new data to fetch")

    print("Data collection complete!")

if __name__ == "__main__":
    main()