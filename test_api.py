import os
import requests
from datetime import datetime

def test_api_connection():
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": f"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDc2MzYzNzgsImV4cCI6MTc0ODg0NTk3OCwiYXV0aF9zZWNyZXQiOiIxOTNlMzRkMTdiY2I0ZmMzYzBjYjc4NzE4NzliODQyZWY0YzU3Mzk1OGI3MTExYzA4NDRiZjA5MmEyYTZmYjIxNTc4NjJhYWQxYmRiNTAyMzc4NjAxNTAwOWM2ZTJjYTU5NTcwY2M3MjRhNDE2YTg3YjM2NDdlZDE3Mjk5NzI5NCJ9.PEhdULJAmfST_wg_Pgj5CnlHV9t52f9lg2OF9e70Rro",
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

    # Use the exact same date and format from the curl command
    params = {
        "from_datetime": "2025-05-19 00:00:00",
        "to_datetime": "2025-05-19 05:00:00",
        "network_code": "PRR"
    }

    url = "https://api.pubplus.com/api/campaigns_report"
    
    try:
        response = requests.get(url, headers=headers, params=params)
        print(f"Status code: {response.status_code}")
        print(f"Request URL: {response.url}")
        print(f"Request headers: {response.request.headers}")
        response.raise_for_status()
        print("Success!")
        print("Response:", response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")

if __name__ == "__main__":
    test_api_connection() 