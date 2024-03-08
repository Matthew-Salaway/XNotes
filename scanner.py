import requests
import os
import json 
from datetime import datetime, timedelta
from dotenv import load_dotenv
load_dotenv()

"""
Fetches the most recent tweets for a particular user. 
We use this to find new tweets that might need to be fact-checked. 
This is still a work-in-progress. 

Ideally, it would:
    1. Include a list of all the users we'd like to regularly fact-check (i.e. 100 popular accounts)
    2. Fetch each user's tweets from the past 24 hours
    a. This should not include retweets or replies
    3. Save them to a CSV file ('new_tweets.csv')
    4. Run a quick check to see if they should be fact-checked
    5. If so, write a note for them, then run the rater on the note.
    6. Update the CSV file with the new note and rating.
"""

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