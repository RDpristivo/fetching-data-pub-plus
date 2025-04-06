from datetime import datetime, timedelta
import time
import os
from get import get_campaign_data
from csv_handler import process_campaigns_data, save_to_csv

def main():
    # Create a parent directory to store campaign data if it doesn't exist
    parent_output_dir = 'campaign_data'
    if not os.path.exists(parent_output_dir):
        os.makedirs(parent_output_dir)
    
    # Create a subdirectory for today's date
    today = datetime.now()
    today_dir = today.strftime('%Y-%m-%d')
    output_dir = os.path.join(parent_output_dir, today_dir)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Loop through the last 30 days
    for day_offset in range(30):
        # Calculate the date
        target_date = today - timedelta(days=day_offset)
        date_str = target_date.strftime('%Y-%m-%d')
        
        # Set time range for the whole day
        start_datetime = f"{date_str} 00:00:00"
        end_datetime = f"{date_str} 23:59:59"
        
        print(f"Fetching data for {date_str}...")
        
        # Get data for this date
        response_data = get_campaign_data(start_datetime, end_datetime)
        
        if response_data:
            # Process the campaigns data into a flat structure
            campaigns_list = process_campaigns_data(response_data)
            
            if campaigns_list:
                # Create filename with date
                filename = os.path.join(output_dir, f"campaign_data_{date_str}.csv")
                
                # Save to CSV
                save_to_csv(campaigns_list, filename)
            else:
                print(f"No campaign data found for {date_str}")
        else:
            print(f"Failed to get data for {date_str}")
        
        # Add a small delay to avoid overwhelming the API
        time.sleep(1)
    
    print("Data collection complete!")

if __name__ == "__main__":
    main()
