import requests
import os
import json 
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

def yesterday_iso_string():
    # Calculate the end_time as one day ago from now
    end_time = datetime.utcnow() - timedelta(days=1)
    end_time_iso8601 = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    end_time_iso8601
    return end_time_iso8601

def get_user_tweets(user_id):
    bearer_token = os.environ.get("BEARER_TOKEN")
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    headers = {'Authorization': f'Bearer {bearer_token}'}
    params = {
        'end_time': yesterday_iso_string(),
        'exclude': 'retweets,replies'
    }
    response = requests.get(url, headers=headers, params=params)
    return response

# Print the status code to verify the request was successful
response = get_user_tweets("44196397")
print(response.status_code)
print(response.text)

response_json = json.loads(response.text)

for d in response_json['data']:
    print(d['text'])