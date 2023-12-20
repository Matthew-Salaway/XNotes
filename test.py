# -*- coding: utf-8 -*-

# Commented out IPython magic to ensure Python compatibility.
# %pip install openai

import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
import os
import openai

os.environ["OPENAI_API_KEY"] = "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"
from openai import OpenAI
client = OpenAI(
  api_key=os.environ["OPENAI_API_KEY"],  # this is also the default, it can be omitted
)


df = pd.read_csv('notes_and_note_status_with_note_text.csv')

df['Links'] = None
df['List of Full Content from Links'] = None
df['List of Shortened Content from Links'] = None

for index, row in df.iterrows():
  #Fetch a tweet
  text = df.iloc[index]['summary']
  url_pattern = re.compile(r'https?://\S+|www\.\S+')

  if bool(url_pattern.search(text)):
    url = re.search("(?P<url>https?://[^\s]+)", text).group("url")
    df.at[index, 'Links'] = url

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    text_content = soup.get_text()
    df.at[index,'List of Full Content from Links'] = text_content

    completion = client.chat.completions.create(
    model="gpt-4",
    messages=[
    {"role": "system", "content": f"Summarize the content in {text_content}"}
    ])
    df.at[index, 'List of Shortened Content from Links'] = completion.choices[0].message
  else:
    df.at[index, 'Links'] = 'N/A'
    df.at[index, 'List of Full Content from Links'] = 'N/A'
    df.at[index, 'List of Shortened Content from Links'] = 'N/A'