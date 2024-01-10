import requests

# Set up the API endpoint with WOEID
# Example: New York City
WOEID = 2459115  # Replace with the WOEID of your desired location
url = f"https://api.twitter.com/2/trends/by/woeid/{WOEID}"

# Use your Bearer Token
headers = {
    "Authorization": "Bearer BEARER_TOKEN"
}

# Make the GET request
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse the response
    trends_data = response.json()
    trends = trends_data.get("data", {}).get("trends", [])
    
    for trend in trends:
        print(trend["name"])
        print(f"Tweet Volume: {trend.get('tweet_volume', 'Not available')}")
        # The v2 API may not provide a direct search URL, so it's omitted here
        print()
else:
    print(f"Failed to fetch trends: {response.status_code}, {response.text}")
