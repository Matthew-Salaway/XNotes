# From these files, we will make a new data frame with the nessary columns for training the Rater model.

# Make a function that uses pandas to import the files in the the Data folder
# and returns a data frame with the necessary columns for training the model.

import pandas as pd
import os
import requests
import json
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

    print(result.head())
    print(result.columns)
    print(result.shape)
    print(result.iloc[1])

def tweet_id_to_text(tweet_id):
    ids = "ids=1278747501642657792,1255542774432063488"
    url = "https://api.twitter.com/2/tweets?{}".format(ids)
    response = requests.request("GET", url, auth=bearer_oauth)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(
            "Request returned an error: {} {}".format(
                response.status_code, response.text
            )
        )
    json_response = response.json()
    print(json.dumps(json_response, indent=4, sort_keys=True))
    return "To be completed"


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2TweetLookupPython"
    return r

if __name__=="__main__":
    # download_datasets_into_data_folder()
    # merge_notes_and_note_status()
    print(bearer_token)
    tweet_id_to_text(1278747501642657792)
