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
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDc2MzYzNzgsImV4cCI6MTc0ODg0NTk3OCwiYXV0aF9zZWNyZXQiOiIxOTNlMzRkMTdiY2I0ZmMzYzBjYjc4NzE4NzliODQyZWY0YzU3Mzk1OGI3MTExYzA4NDRiZjA5MmEyYTZmYjIxNTc4NjJhYWQxYmRiNTAyMzc4NjAxNTAwOWM2ZTJjYTU5NTcwY2M3MjRhNDE2YTg3YjM2NDdlZDE3Mjk5NzI5NCJ9.PEhdULJAmfST_wg_Pgj5CnlHV9t52f9lg2OF9e70Rro",
        "origin": "https://app.pubplus.com",
        "priority": "u=1, i",
        "referer": "https://app.pubplus.com/",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "traceparent": "00-000000000000000014b36b0851fa5160-7dfd6b3569f89aa2-01",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-pp-client-id": "7f156802-18bf-47f1-a8da-719a625fcaca",
        "x-pp-git-version": "c6986e576d509b7e5a53299009ff5792a3455863"
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
