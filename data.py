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
import pdb

bearer_token = os.environ.get("BEARER_TOKEN")

notes_file_path = './Data/notes-00000.tsv'
ratings_1_file_path = './Data/ratings-00000.tsv'
ratings_2_file_path = './Data/ratings-00000.tsv'
note_status_history_file_path = './Data/noteStatusHistory-00000.tsv'
user_enrollment_file_path = './Data/userEnrollment-00000.tsv'

def download_datasets_into_data_folder():
    """
    This function downloads various TSV format datasets from the Community Notes project, 
    which include notes, ratings, note status history, and user enrollment data, and saves 
    them in a newly created 'Data' directory if it doesn't already exist.
    """
    
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

    """
    This function merges 'notes' and 'note status history' data from CSV files into
    a single file, selecting specific columns and saving the result to a new CSV file.
    """
    
    notes_df = pd.read_csv(notes_file_path, sep='\t', usecols=necessary_columns['notes'])
    note_status_df = pd.read_csv(note_status_history_file_path, sep='\t', usecols=necessary_columns.get('noteStatusHistory'))
    result = pd.merge(notes_df, note_status_df, on='noteId').dropna()
    result.to_csv('./Data/notes_and_note_status.csv', index=False)

def filter_out_needs_more_ratings(
        input_path = "./Data/notes_and_note_status.csv", 
        output_path = "./Data/notes_and_note_status_filtered.csv"
    ):
    """
    This function filters out notes that have not yet been rated by enough users.
    """
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
    """
    This function retrieves the text of a tweet using its ID from the Twitter API, 
    handling rate limiting and returning the tweet text.
    """
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
    try: text = json_response['data'][0]['text']
    except: text = None
    return text


def bearer_oauth(r):
    """
    This method is used for bearer token authentication with the Twitter API, 
    setting the necessary headers for the request.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

def fetch_text_for_note_tweets(
        input_path = "./Data/notes_and_note_status_filtered.csv",
        n_tweets = 500, 
        output_path = "./Data/master.csv"
    ):

    """Loops through a CSV of Tweets, fetches the text for each tweet, and saves the file."""

    # Read the CSV
    input_df = pd.read_csv(input_path, dtype={'noteId': str, 'tweetId': str})
    output_df = pd.read_csv(output_path, dtype={'noteId': str, 'tweetId': str})

    # Loop through the dataframe
    for idx, row in input_df.iterrows():
        # Track time for rate limiting
        if idx % 15 == 0: start_time = time.time()

        # Check if we already have the text for this tweet
        tweet_id = row['tweetId']
        if tweet_id in output_df['tweetId'].values: continue

        # If not, fetch the tweet text
        tweet_text = tweet_id_to_text(tweet_id)

        # Append a new row to output_df
        new_row = pd.DataFrame([row])
        new_row['tweet_text'] = tweet_text
        output_df = pd.concat([output_df, new_row], ignore_index=True)

        print(f"New Row: {new_row}")

        # Save the dataframe
        output_df.to_csv(output_path, index=False)
        print(output_df)

        # Sleep for rate limiting
        # Rate limit is 15 requests per 15 minutes
        if idx + 1 % 15 == 0:
            time_elapsed = time.time() - start_time
            time_to_sleep = 60*15 - time_elapsed
            print(f"Sleeping for {time_to_sleep // 60} minutes to avoid rate limiting.")
            time.sleep(time_to_sleep)

        # Break if we've reached the limit
        if idx + 1 == n_tweets: break


if __name__=="__main__":
    # download_datasets_into_data_folder()
    # merge_notes_and_note_status()
    # filter_out_needs_more_ratings()
    fetch_text_for_note_tweets()