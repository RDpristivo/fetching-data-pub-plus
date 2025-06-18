import os
import requests
from datetime import datetime

def test_api_connection():
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": f"Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NTAyNTQ4OTgsImV4cCI6MTc1MTQ2NDQ5OCwiYXV0aF9zZWNyZXQiOiJmM2IyMTYyNjM5OWM1MzQ4YjljZTAwYmY0YWEyZTdiMmY0ZmQ1OGJkZDQ3ZmIwYzczNmYzYTI2MThhM2FjOGVhNTEzZmNhMzZjMmFkY2JiNGZiYmY0YjY5NmM3ZDNhODE0MzM4MTFhYTgyMGE1ZDU0YjE3YjQwNjA1YmM1MDRiNiJ9.16WXln_rdcdBa7mTJFkYAPhkfpSRo-ut1WHlqCwe4k0",
        "origin": "https://app.pubplus.com",
        "priority": "u=1, i",
        "referer": "https://app.pubplus.com/",
        "sec-ch-ua": '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "traceparent": "00-000000000000000066666c748038d1ba-13607ef4efccf2e7-01",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
        "x-pp-client-id": "0b3ae17c-f280-4f21-aecd-8e7ef720ddb7",
        "x-pp-git-version": "56959afe3598d81a9919c57d387e8acda71bad80"
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