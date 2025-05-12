import requests
import os
from dotenv import load_dotenv
from twilio_utils import send_notification_with_fallback

# Load environment variables
load_dotenv()

# Global variable to track if token expiration notification has been sent
token_expiration_notified = False


def get_campaign_data(start_date, end_date):
    """
    Function to fetch campaign data for a specific date range
    """
    url = "https://api.pubplus.com/api/campaigns_report"

    params = {
        "from_datetime": start_date,
        "to_datetime": end_date,
        "network_code": "PRR",
    }

    # Get token from environment variable or use the default one
    token = os.getenv(
        "PUBPLUS_TOKEN",
        "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDYzNjAwNTYsImV4cCI6MTc0NzU2OTY1NiwiYXV0aF9zZWNyZXQiOiJjZTZjMzY2NDMzMWJiYTZkNjc4ZjNhZDc3YjVhOWY0OGQ4NTEyMzhhYWFjMTg3MzAyNmYzNDVlNTU5Zjg3ZDUzNDU1ZDlmOTEyN2IxZjM1OGQ0NDA3NzFmY2Y1MGMwMjg1MDgxMjNkNzMyNDU1OTAwODFiODgwODZjNjEzMDU0NCJ9.VkEucnxkEEVilY425Xua8nL19X3LZ34NgKODr3bIUGQ",
    )

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": f"Bearer {token}",
        "origin": "https://app.pubplus.com",
        "priority": "u=1, i",
        "referer": "https://app.pubplus.com/",
        "sec-ch-ua": '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "x-pp-client-id": "af695b97-301e-45dc-a6af-d00b372e3c4b",
        "x-pp-git-version": "05d1ddf2e7e0c5f07ca063b1bcfd6e5965a17c0a",
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
                error_message = (
                    "❌ PubPlus API token has expired. Please update the token."
                )
                print(error_message)
                send_notification_with_fallback(f"ALERT: {error_message}")
                token_expiration_notified = True
            return None
        else:
            error_message = (
                f"❌ API request failed with status code {response.status_code}"
            )
            print(error_message)
            print(f"Response: {response.text}")
            send_notification_with_fallback(f"ERROR: {error_message}")
            return None
    except Exception as e:
        error_message = f"❌ Exception during API request: {e}"
        print(error_message)
        send_notification_with_fallback(f"ERROR: {error_message}")
        return None
