import pandas as pd
import json

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

def save_to_csv(data, filename):
    """
    Function to save data to a CSV file
    """
    if not data or len(data) == 0:
        print(f"No data to save for {filename}")
        return
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    print(f"Data saved to {filename}")
    print(f"Saved {len(data)} campaigns with {len(df.columns)} columns")
    print(f"First few columns: {', '.join(list(df.columns)[:5])}")
