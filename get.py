import requests

def get_campaign_data(start_date, end_date):
    """
    Function to fetch campaign data for a specific date range
    """
    url = 'https://api.pubplus.com/api/campaigns_report'
    
    params = {
        'from_datetime': start_date,
        'to_datetime': end_date,
        'network_code': 'PRR'
    }
    
    headers = {
        'accept': 'application/json, text/plain, */*',
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDUxMzA5MjgsImV4cCI6MTc0NjM0MDUyOCwiYXV0aF9zZWNyZXQiOiI3OTkzZjcyOTc0YTA0MGZhMmUzMmFmYzI5YjVlMmQyY2M2YjIxZWYxNGU2MTQ1OGU0YTIyZjMxYjA4ZTkzMzcwOTc3MzA3YTg3ZjJhNTA5NjEzMTlkNjM1ZjIwNmE0NmMzNzRhNjY0MmM0NDM5MTM1MjdkYTFmYmE1NDYyOTRlMSJ9.B5nhW32_a7reARCp1jzcXJhyUS7Z5BivIlVQmVTl6Wo',
        'origin': 'https://app.pubplus.com',
        'x-pp-client-id': '65629304-8517-4d74-8416-3d796ce34a3a',
        'x-pp-git-version': 'd0ab415798491ee742976775e3214bceb1f1bb27'
    }

    
    
    response = requests.get(url, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Response: {response.text}")
        return None

# Last Commit | Working