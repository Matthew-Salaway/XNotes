# -*- coding: utf-8 -*-
"""AI Safety.py

## Define the imports
"""

!pip install openai
import openai

import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse
from requests.exceptions import Timeout

"""## Read the data"""

df = pd.read_csv('notes_and_note_status_with_note_text.csv')

"""## Extract all URLs from the given tweet"""

def extract_links_from_text(text):
  # Using regular expression to find all URLs in the text
  urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
  return urls
df['Links'] = None

for index, rows in df.iterrows():
  text = df['summary'][index]
  urls_found = extract_links_from_text(text)
  df.at[index, 'Links'] = urls_found

pd.set_option('display.max_colwidth', None)

# Display the DataFrame
print(df['Links'].head(10))

"""## Extract Text from URLs
## i) Extract text from simple URL
"""

def clean_text(text):
  # Remove unnecessary whitespace and newline characters
  cleaned_text = re.sub(r'\s+', ' ', text).strip()
  return cleaned_text

def extract_text_from_simple_link(url, timeout):
  try:
    # Set a timeout for the request
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
  except Timeout:
    print(f"Request to {url} timed out after {timeout} seconds. Skipping.")
    return None
  except requests.RequestException as e:
    print(f"Error fetching content from {url}: {e}")
    return None

  # Parse the HTML content with BeautifulSoup
  soup = BeautifulSoup(response.content, 'html.parser')
  # Extract text from the HTML
  text_content = soup.get_text()
  return text_content

"""## ii) Extract text from twitter URL"""

import requests
import os

# Set your Twitter API credentials
api_key = "MEoah3xvNazAlSgrX4l6ycz3i"
api_secret_key = "au1H7yB4pBLM9oi7irCRbwH3A36YTuEg0N3TyX5tYveVKdjlYZ"
bearer_token = "AAAAAAAAAAAAAAAAAAAAAL49rAEAAAAAMkVz%2Bw9K69bFPHR7ut6l404vAII%3Dgs4wj1kMlco2iUk3APUEQQZiVPauYbcvuSOvEfmzyk2LSEWNzP"

# Set the Twitter API v2 endpoint
endpoint_url = "https://api.twitter.com/2/tweets"

def fetch_tweet_text(tweet_id):
  try:
    # Set up headers with Bearer Token
    headers = {
        "Authorization": f"Bearer {bearer_token}",
    }

    # Set up parameters
    params = {
        "ids": tweet_id,
        "tweet.fields": "text",
    }

    # Make the request to Twitter API v2
    response = requests.get(endpoint_url, headers=headers, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
      tweet_data = response.json()["data"][0]
      tweet_text = tweet_data["text"]
      return tweet_text
    else:
      return f"Failed to retrieve tweet. Status code: {response.status_code}"
  except Exception as e:
    return f"An error occurred: {e}"

"""## Check if a url is a twitter URl or not"""

def is_twitter_url(url):
  # Regular expression pattern for matching Twitter URLs
  twitter_pattern = r'https?://twitter\.com/([^/]+)/status/(\d+)'
  # Check if the URL matches the Twitter pattern
  match = re.match(twitter_pattern, url)
  return bool(match)

"""## Select first 1000 words of a sentence"""

import nltk
from nltk.tokenize import word_tokenize
nltk.download('punkt')  # Download the tokenizer models

def select_first_1000_words(sentence):
  # Tokenize the sentence into words
  words = word_tokenize(sentence)
  # Select the first 1000 words
  selected_words = words[:1000]
  # Join the selected words back into a sentence
  selected_sentence = ' '.join(selected_words)
  return selected_sentence

def count_words(input_string):
    words = input_string.split()
    return len(words)

"""## Iterate through the dataset and extract text"""

df['List of Full Content from Links'] = None

for index, rows in df.iterrows():
  print(index)
  urls = df['Links'][index]
  text_contents = []
  if urls:
    for url in urls:
      if is_twitter_url(url):
        tweet_id = url.split("/")[-1]
        # Fetch text from the Twitter link using the Twitter API v2
        text = fetch_tweet_text(tweet_id)
        text_contents.append(text)
      else:
        content = extract_text_from_simple_link(url=url, timeout=10)
        if content != None:
          content = clean_text(content)
          content = select_first_1000_words(content)
        text_contents.append(content)
      df.at[index,'List of Full Content from Links'] = text_contents
  else:
    df.at[index,'List of Full Content from Links'] = None

print(df['List of Full Content from Links'][3])

!pip install langid
import langid

def is_english(text):
    # Detect the language of the text
    lang, _ = langid.classify(text)

    # Check if the detected language is English
    return lang == 'en'

def summarize_text_content(text_content):
  os.environ["OPENAI_API_KEY"] = "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"
  from openai import OpenAI
  client = OpenAI(
    api_key=os.environ["OPENAI_API_KEY"],  # this is also the default, it can be omitted
  )

  if is_english(text_content):
    completion = client.chat.completions.create(
      model="gpt-4",
      messages=[
      {"role": "system", "content": f"Summarize the content in {text_content} in about 200-300 words"}
      ])
    return completion.choices[0].message.content
  else:
    return None

df['List of Shortened Content from Links']=None
for index, rows in df.iterrows():
  print(index)
  summarized_content=[]
  content = df['List of Full Content from Links'][index]
  print(content)
  if content != None:
    for text in content:
      if text != None:
        summary = summarize_text_content(text)
        summarized_content.append(summary)
      else:
        summary = None
        summarized_content.append(summary)
    df.at[index,'List of Shortened Content from Links']=summarized_content
    print(summarized_content)
  else:
    df.at[index,'List of Shortened Content from Links']=None

"""## Convert the dataframe to CSV File"""

df.to_csv('summary.csv')