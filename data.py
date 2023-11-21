# From these files, we will make a new data frame with the nessary columns for training the Rater model.

# Make a function that uses pandas to import the files in the the Data folder
# and returns a data frame with the necessary columns for training the model.

import pandas as pd
import os
import requests
import json
import time
from dotenv import load_dotenv
load_dotenv()

# Do we need more? 
bearer_token = os.environ.get("BEARER_TOKEN")

notes_file_path = './Data/notes-00000.tsv'
ratings_1_file_path = './Data/ratings-00000.tsv'
ratings_2_file_path = './Data/ratings-00000.tsv'
note_status_history_file_path = './Data/noteStatusHistory-00000.tsv'
user_enrollment_file_path = './Data/userEnrollment-00000.tsv'

def download_datasets_into_data_folder():
    """Downloads the Community Notes datasets"""
    links = [
    'https://ton.twimg.com/birdwatch-public-data/2023/11/01/notes/notes-00000.tsv',
    'https://ton.twimg.com/birdwatch-public-data/2023/11/01/noteRatings/ratings-00001.tsv',
    'https://ton.twimg.com/birdwatch-public-data/2023/11/01/noteRatings/ratings-00000.tsv',
    'https://ton.twimg.com/birdwatch-public-data/2023/11/01/noteStatusHistory/noteStatusHistory-00000.tsv',
    'https://ton.twimg.com/birdwatch-public-data/2023/11/01/userEnrollment/userEnrollment-00000.tsv'
    ]
    data_directory = 'Data'
    # Create the directory if it doesn't exist
    if not os.path.exists(data_directory):
        os.makedirs(data_directory)

    # Nested function to download and save a file
    def download_file(url, folder):
        local_filename = url.split('/')[-1]
        local_filepath = os.path.join(folder, local_filename)

        # Stream the download (for large files)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

        return local_filepath

    # Download each file
    for link in links:
        try:
            filepath = download_file(link, data_directory)
            print(f"Downloaded {link} to {filepath}")
        except requests.exceptions.HTTPError as err:
            print(f"Failed to download {link}: {err}")

def merge_notes_and_note_status(
        necessary_columns = {"notes": ['noteId', 'tweetId', 'summary'], 
        "noteStatusHistory": ['noteId', 'currentStatus'],}
    ):
    
    notes_df = pd.read_csv(notes_file_path, sep='\t', usecols=necessary_columns['notes'])
    note_status_df = pd.read_csv(note_status_history_file_path, sep='\t', usecols=necessary_columns.get('noteStatusHistory'))
    result = pd.merge(notes_df, note_status_df, on='noteId').dropna()
    result.to_csv('./Data/notes_and_note_status.csv', index=False)

def filter_out_needs_more_ratings(
        input_path = "./Data/notes_and_note_status.csv", 
        output_path = "./Data/notes_and_note_status_filtered.csv"
    ):
    # Alternate between helpful statuses
    good_statuses = ["CURRENTLY_RATED_HELPFUL", "CURRENTLY_RATED_NOT_HELPFUL"]
    current_status = 0

    df = pd.read_csv(input_path)
    output_df = pd.DataFrame(columns=['noteId', 'tweetId', 'summary', 'currentStatus'])

    for idx, row in df.iterrows():
        if row['currentStatus'] == good_statuses[current_status]:
            current_status = (current_status + 1) % 2
            output_df = pd.concat([output_df, row.to_frame().transpose()])

    output_df.to_csv(output_path, index=False)
    

def tweet_id_to_text(tweet_id):
    print(f"Tweet ID: {tweet_id}")
    url = "https://api.twitter.com/2/tweets?ids={}".format(tweet_id)
    response = requests.request("GET", url, auth=bearer_oauth)
    print(response.status_code)

    while response.status_code == 429:
        sleep_time = 60
        print(f"Too many requests! Sleeping for {sleep_time} seconds.")
        time.sleep(sleep_time)
        response = requests.request("GET", url, auth=bearer_oauth)

    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )

    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))
    text = json_response['data'][0]['text']
    return text


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r


def fetch_text_for_note_tweets(
        input_path = "./Data/notes_and_note_status.csv",
        n_tweets = 1000, 
        output_path = "./Data/notes_and_note_status_with_note_text.csv"
    ):

    """Loops through a CSV of Tweets, fetches the text for each tweet, and saves the file."""

    # Read the CSV
    df = pd.read_csv(input_path)
    output_df = pd.DataFrame(columns=['noteId', 'tweetId', 'summary', 'currentStatus', 'tweet_text'])

    # Loop through the dataframe
    for idx, row in df.iterrows():
        # Fetch the tweet text
        tweet_id = row['tweetId']
        tweet_text = tweet_id_to_text(tweet_id)

        # Append a new row to output_df
        new_row = pd.DataFrame([row])
        new_row['tweet_text'] = tweet_text
        output_df = pd.concat([output_df, new_row], ignore_index=True)

        # Save the dataframe
        output_df.to_csv(output_path, index=False)
        print(output_df)

        # Sleep for rate limiting
        # Rate limit is 15 requests per 15 minutes
        print(f"Sleeping for 60 seconds to avoid rate limiting.")
        time.sleep(60)

        # Break if we've reached the limit
        if idx + 1 == n_tweets: break


if __name__=="__main__":
    # download_datasets_into_data_folder()
    # merge_notes_and_note_status()
    filter_out_needs_more_ratings()
    # tweet_id_to_text(1278747501642657792)
    # fetch_text_for_note_tweets()