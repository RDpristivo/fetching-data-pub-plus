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
    upload_df_to_drive,
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
    output_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "campaign_data")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"ℹ️ Created local directory: {output_dir}")

    # Define the single CSV file path using os.path.join
    filename = os.path.join(output_dir, "pubplus_campaign_data.csv")

    # Get current date and calculate start date (30 days ago)
    today = datetime.now()
    start_date = today - timedelta(days=7)
    print(f"ℹ️ Fetching data from {start_date.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}")

    all_campaigns = []
    successful_days = 0
    failed_days = 0
    empty_days = 0

    # Fetch data for each day in the last 7 days
    current_date = start_date
    campaigns_by_date = {}  # Dictionary to track campaigns per date
    
    while current_date <= today:
        date_str = current_date.strftime("%Y-%m-%d")
        
        # Set time range for the entire day
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
                campaigns_by_date[date_str] = len(campaigns_list)
                print(f"✅ Successfully processed {len(campaigns_list)} campaigns for {date_str}")
            else:
                empty_days += 1
                campaigns_by_date[date_str] = 0
                print(f"⚠️ No campaign data found for {date_str}")
        else:
            failed_days += 1
            campaigns_by_date[date_str] = 0
            print(f"❌ Failed to fetch data for {date_str}")

        current_date += timedelta(days=1)

        # Add delay between days to avoid rate limiting
        if current_date <= today:
            print("ℹ️ Waiting before next request...")
            time.sleep(5)  # Add 5 second delay between requests

    # Summary of data collection
    print(f"\n📊 Data collection summary:")
    print(f"  ✅ Successful days: {successful_days}")
    print(f"  ⚠️ Empty days: {empty_days}")
    print(f"  ❌ Failed days: {failed_days}")
    print(f"  📋 Total campaigns collected: {len(all_campaigns)}")
    
    # Print campaigns per date
    print("\n📅 Campaigns per date:")
    for date, count in sorted(campaigns_by_date.items()):
        print(f"  {date}: {count} campaigns")

    if all_campaigns:
        # Upload to Google Drive
        try:
            print(f"ℹ️ Uploading data to Google Drive...")
            
            # First save to CSV
            save_to_csv(all_campaigns, filename)
            print(f"✅ Saved data to local CSV: {filename}")
            
            # Create DataFrame directly from all_campaigns
            df = pd.DataFrame(all_campaigns)
            
            # Upload DataFrame directly
            file_id = upload_df_to_drive(drive_service, sheets_service, df, drive_folder_id)
            
            if file_id:
                success_message = f"✅ Data successfully updated in Google Drive spreadsheet"
                print(success_message)
                # Send success notification
                send_notification_with_fallback(
                    f"SUCCESS: PubPlus data collection complete. Updated {successful_days} days of data. ({empty_days} empty, {failed_days} failed)"
                )
            else:
                error_message = "❌ Failed to update Google Drive spreadsheet - file not found"
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

def save_to_csv(campaigns, filename):
    """Save campaign data to CSV file"""
    try:
        # Debug print raw data
        print("\n🔍 Debug - Raw data before DataFrame conversion:")
        print(f"  Number of campaigns: {len(campaigns)}")
        date_counts = {}
        for campaign in campaigns:
            date = campaign['date']
            date_counts[date] = date_counts.get(date, 0) + 1
        
        print("  Date distribution in raw data:")
        for date in sorted(date_counts.keys()):
            print(f"    {date}: {date_counts[date]} campaigns")
        
        # Convert list of dictionaries to DataFrame
        df = pd.DataFrame(campaigns)
        
        # Debug print before saving
        print("\n🔍 Debug - Data being saved to CSV:")
        print(f"  Date range in memory: {df['date'].min()} to {df['date'].max()}")
        print(f"  Total rows: {len(df)}")
        
        # Save to CSV with explicit date format
        df.to_csv(filename, index=False, date_format='%Y-%m-%d')
        print(f"Saved {len(df)} rows to {filename}")
        
        # Verify saved data
        df_check = pd.read_csv(filename)
        print("\n🔍 Debug - Verification after save:")
        print(f"  Date range in saved file: {df_check['date'].min()} to {df_check['date'].max()}")
        print(f"  Total rows in file: {len(df_check)}")
        
        # Check for date format issues
        print("\n🔍 Debug - Date format check:")
        date_samples = df_check['date'].sample(min(5, len(df_check))).tolist()
        print(f"  Sample dates from file: {date_samples}")
        
        # Verify all dates are present
        date_counts_in_file = df_check['date'].value_counts().to_dict()
        print(f"  Number of unique dates in file: {len(date_counts_in_file)}")
        
        # Check for missing dates
        missing_dates = []
        for date in date_counts:
            if date not in date_counts_in_file:
                missing_dates.append(date)
        
        if missing_dates:
            print(f"⚠️ WARNING: {len(missing_dates)} dates are missing in the saved file!")
            print(f"  Missing dates: {missing_dates}")
        else:
            print("✅ All dates from raw data are present in the saved file")
        
        return df_check  # Return the dataframe for direct use
        
    except Exception as e:
        error_message = f"❌ Error saving to CSV: {e}"
        print(error_message)
        send_notification_with_fallback(f"ERROR: {error_message}")
        return None
