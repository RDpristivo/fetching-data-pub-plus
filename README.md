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

## Technical Details

- Uses cURL for API requests
- Processes CSV response format
- Maintains 30-day rolling window of data

---

For internal use only
