# fetching-data-pub-plus

## Purpose

Service that fetches campaign data from Pub+ API using cURL requests. The service retrieves CSV files containing campaign performance data for the last 30 days.

## Features

- Automated daily data retrieval via cURL requests
- Fetches CSV files for each day (30-day historical data)
- Handles Pub+ API authentication and responses
- Processes campaign performance metrics

## Data Collection

- Retrieves data for the past 30 days
- Each request returns a CSV file with daily campaign data
- Automatically handles API rate limits and retries

## Configuration

Requires Pub+ API credentials and endpoint configuration for successful data retrieval.

## Credentials Setup

1. Copy `credentials.json.example` to `credentials.json`
2. Replace the placeholder values with your actual Google OAuth credentials
3. Never commit `credentials.json` to version control

## Technical Details

- Uses cURL for API requests
- Processes CSV response format
- Maintains 30-day rolling window of data

---

For internal use only
