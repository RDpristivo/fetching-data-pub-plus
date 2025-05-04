import requests


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

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en",
        "authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDYzNjAwNTYsImV4cCI6MTc0NzU2OTY1NiwiYXV0aF9zZWNyZXQiOiJjZTZjMzY2NDMzMWJiYTZkNjc4ZjNhZDc3YjVhOWY0OGQ4NTEyMzhhYWFjMTg3MzAyNmYzNDVlNTU5Zjg3ZDUzNDU1ZDlmOTEyN2IxZjM1OGQ0NDA3NzFmY2Y1MGMwMjg1MDgxMjNkNzMyNDU1OTAwODFiODgwODZjNjEzMDU0NCJ9.VkEucnxkEEVilY425Xua8nL19X3LZ34NgKODr3bIUGQ",
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
        "x-pp-client-id": "dc962049-34f7-4110-b41e-173cb8c388d7",
        "x-pp-git-version": "e9178bcaaa83d93f31deee33ee8228ea92862808",
    }

    response = requests.get(url, params=params, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return None


# Last Commit | Working - Updated with new cURL details on May 4, 2025
