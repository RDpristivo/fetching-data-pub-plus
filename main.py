from datetime import datetime, timedelta
import time
import os
import pandas as pd
from dotenv import load_dotenv
from get import get_campaign_data
from csv_handler import process_campaigns_data, save_to_csv
from drive_handler import (
    get_google_drive_service,
    create_folder_if_not_exists,
    upload_csv_to_drive,
)
from twilio_utils import send_notification_with_fallback

# Load environment variables
load_dotenv()


def main():
    print("\n🔄 Starting PubPlus campaign data collection...")

    # Initialize Google Drive and Sheets services
    try:
        drive_service, sheets_service = get_google_drive_service()
        print("✅ Successfully connected to Google services")
    except Exception as e:
        error_message = f"❌ Error connecting to Google services: {e}"
        print(error_message)
        print("Please check your Google API credentials and internet connection.")
        send_notification_with_fallback(f"ALERT: {error_message}")
        return

    # Create or get the main campaign_data folder in Google Drive
    try:
        drive_folder_id = create_folder_if_not_exists(drive_service, "campaign_data")
        print(f"ℹ️ Using Google Drive folder: campaign_data (ID: {drive_folder_id})")
    except Exception as e:
        error_message = f"❌ Error accessing Google Drive folder: {e}"
        print(error_message)
        send_notification_with_fallback(f"ALERT: {error_message}")
        return

    # Create directory for data if it doesn't exist
    output_dir = "campaign_data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"ℹ️ Created local directory: {output_dir}")

    # Define the single CSV file path
    filename = os.path.join(output_dir, "pubplus_campaign_data.csv")

    # Get current date and calculate start date (30 days ago)
    today = datetime.now()
    start_date = today - timedelta(days=29)
    print(
        f"ℹ️ Fetching data from {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
    )

    all_campaigns = []
    successful_days = 0
    failed_days = 0
    empty_days = 0

    # Fetch data for each day in the last 30 days
    current_date = start_date
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        start_datetime = f"{date_str} 00:00:00"
        end_datetime = f"{date_str} 23:59:59"

        print(f"\nℹ️ Fetching data for {date_str}...")

        response_data = get_campaign_data(start_datetime, end_datetime)

        if response_data:
            campaigns_list = process_campaigns_data(response_data)
            if campaigns_list and len(campaigns_list) > 0:
                for campaign in campaigns_list:
                    campaign["date"] = date_str
                all_campaigns.extend(campaigns_list)
                successful_days += 1
                print(
                    f"✅ Successfully processed {len(campaigns_list)} campaigns for {date_str}"
                )
            else:
                empty_days += 1
                print(f"⚠️ No campaign data found for {date_str}")
        else:
            failed_days += 1
            print(f"❌ Failed to fetch data for {date_str}")

        current_date += timedelta(days=1)

        # Add delay between requests to avoid rate limiting
        if current_date <= today:
            print("ℹ️ Waiting before next request...")
            time.sleep(2)  # Add 2 second delay between requests

    # Summary of data collection
    print(f"\n📊 Data collection summary:")
    print(f"  ✅ Successful days: {successful_days}")
    print(f"  ⚠️ Empty days: {empty_days}")
    print(f"  ❌ Failed days: {failed_days}")
    print(f"  📋 Total campaigns collected: {len(all_campaigns)}")

    if all_campaigns:
        # Save/update local CSV
        save_to_csv(all_campaigns, filename)
        print(f"✅ Saved data to local CSV: {filename}")

        # Upload to Google Drive
        try:
            print(f"ℹ️ Uploading data to Google Drive...")
            file_id = upload_csv_to_drive(
                drive_service, sheets_service, filename, drive_folder_id
            )

            if file_id:
                success_message = (
                    f"✅ Data successfully updated in Google Drive spreadsheet"
                )
                print(success_message)
                # Send success notification
                send_notification_with_fallback(
                    f"SUCCESS: PubPlus data collection complete. Updated {successful_days} days of data. ({empty_days} empty, {failed_days} failed)"
                )
            else:
                error_message = (
                    "❌ Failed to update Google Drive spreadsheet - file not found"
                )
                print(error_message)
                send_notification_with_fallback(f"ALERT: {error_message}")
        except Exception as e:
            error_message = f"❌ Error uploading to Google Drive: {e}"
            print(error_message)
            send_notification_with_fallback(f"ALERT: {error_message}")
    else:
        error_message = "⚠️ No data to upload to Google Drive"
        print(error_message)
        send_notification_with_fallback(f"WARNING: {error_message}")

    print("\n✅ Data collection process complete!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_message = f"❌ CRITICAL ERROR: {e}"
        print(error_message)
        send_notification_with_fallback(f"CRITICAL ERROR: {error_message}")
