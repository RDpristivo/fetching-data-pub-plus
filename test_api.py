import os
import requests
from datetime import datetime

def test_api_connection():
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": f"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTI2MTY3MDgsImV4cCI6MTc1MzgyNjMwOCwiYXV0aF9zZWNyZXQiOiI1ZTUxMzAwOTQwNzRlOTEyY2FiYTNiNmE5MzU5MTYwN2ZlNmJlMGY0ZWQ2ZTUxMzE1ZTA2ODliOTYyZDM2NjEwNGM3YjEyZmY5MmIyZmRkNTg2MDUwYjdmNTUxY2I4MTc2NWMzN2FkYWIwNTU4N2U1MWZjNWJmZTJjZGRiMzhhOSJ9.fQ-hK_vltvawZHVDvAKOgP4ocdGWQhbwq9d1wiQmtAs",
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

    # Use the exact same date and format from the curl command
    params = {
        "from_datetime": "2025-07-16 00:00:00",
        "to_datetime": "2025-07-16 08:00:00",
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