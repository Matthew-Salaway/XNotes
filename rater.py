import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm

from dotenv import load_dotenv
dotenv_path = Path('/Users/adityajadhav/Downloads/Rater/notes.env')
load_dotenv(dotenv_path=dotenv_path)

df = pd.read_csv('notes_and_note_status_with_note_text.csv')
df = df.reset_index()
df["isNoteHelpful?"]=0
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_prediction(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['summary']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )

        if response.choices[0].message.content == 'Yes':
            dataset.at[index,'isNoteHelpful?'] = 1
        else:
            dataset.at[index,'isNoteHelpful?'] = 0
    return dataset

def to_csv(dataset):
    dataset.to_csv('note_ratings.csv',index=False)

def evaluate(dataset):
    correct = 0
    total = 0
    for index, row in dataset.iterrows():
        if row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL' and row['isNoteHelpful?']==1:
            correct += 1
        elif row['currentStatus'] == 'CURRENTLY_RATED_NOT_HELPFUL' and row['isNoteHelpful?']==0:
            correct += 1
        total += 1

    accuracy = (correct/total)*100
    return accuracy

ratings_df = generate_prediction(df)
to_csv(ratings_df)
accuracy = evaluate(ratings_df)
print('-'*50 + 'Accuracy' + '-'*50)
print(accuracy)