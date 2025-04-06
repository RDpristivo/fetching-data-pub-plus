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
        'authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3NDM2ODk0MDUsImV4cCI6MTc0NDg5OTAwNSwiYXV0aF9zZWNyZXQiOiIwZTA3MzU1YWY1MTAwZjliNGU4NmFkN2E4NTE1Zjk5ZTIwNWVkOTBkNmZkNzE0YjdkMmMxZWRkODI5OTY1NzIyNjJlZTZmYzk5NWIwYWRjZTY5NGNiMjk5NTU1OGExYjljNjJkMmJhYThkYzExMjNhOGRkOTJkMjZlNzlkNWE2OCJ9.xg9h8kA1FIZeQSgRg01uuekaLiJVNbtdtObRYtYBSaQ',
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
