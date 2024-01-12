import re
import requests
from bs4 import BeautifulSoup
from nltk.metrics import edit_distance
from dotenv import load_dotenv
from data import tweet_id_to_text
load_dotenv()

def extract_links_from_text(text):
  # Using regular expression to find all URLs in the text
  text = str(text)
  urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', str(text))
  return urls

def is_twitter_url(url):
  return ("twitter.com" in url and "/status/" in url)

def extract_status_id(url: str) -> str:
  # find the Tweet ID from a tweet URL
  start_index = url.find("/status/")
  start_index += len("/status/")
  end_index = url.find("/", start_index+1)
  return url[start_index:end_index] if end_index != -1 else url[start_index:]

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

def clean_text(text):
  # Remove unnecessary whitespace and newline characters
  cleaned_text = re.sub(r'\s+', ' ', text).strip()
  return cleaned_text

def count_words(input_string):
  words = input_string.split()
  return len(words)

def select_first_1000_words(text):
  text_pieces = text.split()
  shortened_text_pieces = text_pieces[:1000]
  shortened_text = ' '.join(shortened_text_pieces)
  return shortened_text



def unfurl_links(text):
  """
  Given text which may contain links, fetch the content of those links
  and incorporate the content into the body of the original text. 
  """
  # Use regex to extract all links from the text
  links = extract_links_from_text(text)
  media_flag = False

  for url in links:
    # Sometimes a link redirects to another link, so we need to follow the redirect
    redirected_url = requests.get(url).url
    # Links to other Tweets require authentication via the Twitter API
    if is_twitter_url(redirected_url): # TODO: Check this works
      tweet_id = extract_status_id(redirected_url)
      tweet_text = tweet_id_to_text(tweet_id)

      # Links to photos and videos will return the same text as the original tweet
      if edit_distance(tweet_text, text) < 10: 
        media_flag = True
      else: content = tweet_text
    
    # Links to all other sources are fetched with the requests library
    else:
      link_text = extract_text_from_simple_link(redirected_url, timeout=10)
      # And shortened to their first 1000 words
      link_text = clean_text(link_text)
      link_text = select_first_1000_words(link_text)
      content = link_text
    
    # Replace each link with its content
    if media_flag==False: replacement_text = f"\n\nLink to: {redirected_url}\n\nContent from Link: {content}\n\n"
    else: replacement_text = "\n\nWARNING: This tweet contains an image or video that cannot be displayed.\n\n"
    text = text.replace(url, replacement_text)

  return text