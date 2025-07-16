import requests
import os
from dotenv import load_dotenv
from twilio_utils import send_notification_with_fallback

# Load environment variables
load_dotenv()

# Global variable to track if token expiration notified
token_expiration_notified = False


def get_campaign_data(start_date, end_date):
    """
    Function to fetch campaign data for a specific date range
    """
    url = "https://api.pubplus.com/api/campaigns_report"

    params = {
        "from_datetime": start_date,
        "to_datetime": end_date,
        "network_code": "PRR"
    }

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTI2MTY3MDgsImV4cCI6MTc1MzgyNjMwOCwiYXV0aF9zZWNyZXQiOiI1ZTUxMzAwOTQwNzRlOTEyY2FiYTNiNmE5MzU5MTYwN2ZlNmJlMGY0ZWQ2ZTUxMzE1ZTA2ODliOTYyZDM2NjEwNGM3YjEyZmY5MmIyZmRkNTg2MDUwYjdmNTUxY2I4MTc2NWMzN2FkYWIwNTU4N2U1MWZjNWJmZTJjZGRiMzhhOSJ9.fQ-hK_vltvawZHVDvAKOgP4ocdGWQhbwq9d1wiQmtAs",
        "origin": "https://app.pubplus.com",
        "priority": "u=1, i",
        "referer": "https://app.pubplus.com/",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "traceparent": "00-000000000000000046ac238b662a201d-41c6e080bda93a37-01",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "x-pp-client-id": "73dd656c-09f0-418f-a44a-3381a49569b6",
        "x-pp-git-version": "a573203488ab6d3c213fac0943bab8584f465dd5"
    }

    try:
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            print(f"✅ API request successful for {start_date} to {end_date}")
            return response.json()
        elif response.status_code in (401, 403):
            # Token has likely expired
            global token_expiration_notified
            if not token_expiration_notified:
                error_message = "❌ PubPlus API token has expired. Please update the token."
                print(error_message)
                send_notification_with_fallback(f"ALERT: {error_message}")
                token_expiration_notified = True
            return None
        else:
            error_message = f"❌ API request failed with status code {response.status_code}"
            print(error_message)
            print(f"Response: {response.text}")
            send_notification_with_fallback(f"ERROR: {error_message}")
            return None
    except Exception as e:
        error_message = f"❌ Exception during API request: {e}"
        print(error_message)
        send_notification_with_fallback(f"ERROR: {error_message}")
        return None

def process_campaigns_data(response_data):
    """Process the raw campaign data into a list of dictionaries"""
    try:
        campaigns_list = []
        
        # Debug print
        print("\n🔍 Debug - Processing campaign data:")
        print(f"  Number of campaigns in response: {len(response_data)}")
        
        for campaign in response_data:
            processed_campaign = {
                "campaign_id": campaign.get("campaign_id", ""),
                "campaign_name": campaign.get("campaign_name", ""),
                "date": campaign.get("date", ""),  # Make sure date is being set correctly
                "impressions": campaign.get("impressions", 0),
                "clicks": campaign.get("clicks", 0),
                "ctr": campaign.get("ctr", 0),
                "revenue": campaign.get("revenue", 0),
                "ecpm": campaign.get("ecpm", 0),
                "profit": campaign.get("profit", 0),
                "margin": campaign.get("margin", 0),
                "cpc": campaign.get("cpc", 0),
                "network": campaign.get("network", ""),
                "network_account_id": campaign.get("network_account_id", ""),
                "network_placement_id": campaign.get("network_placement_id", ""),
                "network_app_id": campaign.get("network_app_id", ""),
                "network_campaign_id": campaign.get("network_campaign_id", ""),
                "network_campaign_name": campaign.get("network_campaign_name", ""),
                "network_placement_name": campaign.get("network_placement_name", ""),
                "network_app_name": campaign.get("network_app_name", ""),
                "network_account_name": campaign.get("network_account_name", ""),
            }
            campaigns_list.append(processed_campaign)
            
        # Debug print sample of processed data
        if campaigns_list:
            print(f"  Sample campaign dates:")
            for i, campaign in enumerate(campaigns_list[:5]):
                print(f"    Campaign {i+1}: {campaign['date']}")
                
        return campaigns_list
    except Exception as e:
        error_message = f"❌ Error processing campaign data: {e}"
        print(error_message)
        send_notification_with_fallback(f"ERROR: {error_message}")
        return None
