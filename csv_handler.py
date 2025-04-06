import os
import pandas as pd
import json
from datetime import datetime, timedelta

def process_campaigns_data(data):
    """
    Process the nested campaigns data structure into a flat list of dictionaries
    """
    campaigns_list = []
    
    if not data or 'report' not in data:
        print("Error: Data doesn't contain 'report' key")
        return campaigns_list
    
    report = data['report']
    
    for campaign_id, campaign_data in report.items():
        campaign_data['campaign_id'] = campaign_id
        
        if 'url_params' in campaign_data and isinstance(campaign_data['url_params'], dict):
            for key, value in campaign_data['url_params'].items():
                campaign_data[f'url_param_{key}'] = value
        
        if 'targeting' in campaign_data and isinstance(campaign_data['targeting'], dict):
            for key, value in campaign_data['targeting'].items():
                if isinstance(value, (str, int, float, bool)):
                    campaign_data[f'targeting_{key}'] = value
                elif isinstance(value, list):
                    campaign_data[f'targeting_{key}'] = ', '.join(str(v) for v in value)
                else:
                    campaign_data[f'targeting_{key}'] = json.dumps(value)
        
        for nested_key in ['ads_status', 'last_modified_action']:
            if nested_key in campaign_data and isinstance(campaign_data[nested_key], dict):
                for key, value in campaign_data[nested_key].items():
                    campaign_data[f'{nested_key}_{key}'] = value
        
        campaigns_list.append(campaign_data)
    
    return campaigns_list

def load_existing_csv(filename):
    """
    Load existing CSV file into a pandas DataFrame
    If file doesn't exist, return empty DataFrame with the exact required header columns
    """
    try:
        return pd.read_csv(filename)
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "date",
            "feed",
            "campaign_id",
            "status",
            "daily_budget",
            "activation_date",
            "revenue",
            "page_views",
            "visits",
            "clicks",
            "roi",
            "cost_per_click",
            "profit",
            "bid_strategy",
            "learning_stage_info",
            "site_name",
            "results",
            "results_rate",
            "ads_status",
            "keyword_impressions",
            "searches",
            "visit_roi",
            "fetched_timestamp"
        ])

def save_to_csv(data, filename):
    """
    Function to save or update data in a CSV file
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    if not data or len(data) == 0:
        print(f"No data to save for {filename}")
        return

    # Convert new data to DataFrame and add timestamp
    new_df = pd.DataFrame(data)
    new_df['fetched_timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_df['feed'] = 'pubplus'  # Add feed column with default value

    # Load existing data (will have proper header if file exists)
    existing_df = load_existing_csv(filename)

    # Create a unique key from date and campaign_id for update detection.
    new_df['unique_key'] = new_df['date'].astype(str) + '_' + new_df['campaign_id'].astype(str)
    if not existing_df.empty:
        existing_df['unique_key'] = existing_df['date'].astype(str) + '_' + existing_df['campaign_id'].astype(str)

    # Remove existing rows that are being updated in new_df (same date and campaign_id)
    if not existing_df.empty:
        existing_df = existing_df[~existing_df['unique_key'].isin(new_df['unique_key'])]

    # Combine existing and new data
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df.drop(columns='unique_key', inplace=True)

    # Sort by date and campaign_id as needed
    combined_df.sort_values(by=['date', 'campaign_id'], inplace=True)
    
    # Filter to keep only rows from the last 30 days
    cutoff_date = datetime.now() - timedelta(days=29)
    combined_df['date'] = pd.to_datetime(combined_df['date'], errors='coerce')
    combined_df = combined_df[combined_df['date'] >= cutoff_date]
    combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')
    
    # Save the combined data with the exact header columns as required.
    combined_df.to_csv(filename, index=False)
