import openai

import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urlparse
from requests.exceptions import Timeout
from openai import OpenAI

def extract_links_from_text(text):
  # Using regular expression to find all URLs in the text
  text = str(text)
  urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(text))
  return urls

def clean_text(text):
  # Remove unnecessary whitespace and newline characters
  cleaned_text = re.sub(r'\s+', ' ', text).strip()
  return cleaned_text

def extract_text_from_simple_link(url, timeout):
  try:
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()  # Raise an exception for 4xx and 5xx status codes
  except: return "ERROR: The link text could not be retrieved."

  # Parse the HTML content with BeautifulSoup
  soup = BeautifulSoup(response.content, 'html.parser')
  # Extract text from the HTML
  text_content = soup.get_text()
  return text_content

# TODO: ELIMINATE THIS FUNCTION. Use tweet_id_to_text() in data.py
def fetch_tweet_text(tweet_id):
  try:
    
    endpoint_url = "https://api.twitter.com/2/tweets"
    headers = {"Authorization": f"Bearer {bearer_token}"}
    params = {
        "ids": tweet_id,
        "tweet.fields": "text",
    }
    response = requests.get(endpoint_url, headers=headers, params=params)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
      tweet_data = response.json()["data"][0]
      tweet_text = tweet_data["text"]
      return tweet_text
    else:
      return f"Failed to retrieve tweet. Status code: {response.status_code}"
  except Exception as e:
    # TODO: Monitor for errors here, and potentially fix them
    # Causes: Rate limiting. No wifi or something. Incorrect bearer token. 
    return f"An error occurred: {e}"

def is_twitter_url(url):
  # Regular expression pattern for matching Twitter URLs
  twitter_pattern = r'https?://(?:www\.)?(twitter\.com|t\.co)/'
  match = re.match(twitter_pattern, url)
  return bool(match)

def select_first_1000_words(text):
  text_pieces = text.split()
  shortened_text_pieces = text_pieces[:1000]
  shortened_text = ' '.join(shortened_text_pieces)
  return shortened_text

def count_words(input_string):
  words = input_string.split()
  return len(words)

def summarize_text_content(text_content):
  # TODO: Use our standard API call
  client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY")) 
  completion = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": f"Briefly summarize the following content:\n\n{text_content}"}]
  )
  return completion.choices[0].message.content


if __name__=="__main__":
  
  bearer_token = os.environ.get("BEARER_TOKEN")

  df = pd.read_csv('Data/master.csv')
  df['Links'] = None

  for index, rows in df.iterrows():
    text = df['tweet_text'][index]
    urls_found = extract_links_from_text(text)
    df.at[index, 'Links'] = urls_found

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
          # TODO: What happens if this is an image or a video? 
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

  df.to_csv('summary.csv')