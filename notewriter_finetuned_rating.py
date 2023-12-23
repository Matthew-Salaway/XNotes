import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def generate_prediction_for_note_finetuned(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['note_finetuned']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

        response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )

        if response.choices[0].message.content == 'Yes':
            dataset.at[index,'rating_of_note_finetuned_rater_zero_shot'] = 1
        else:
            dataset.at[index,'rating_of_note_finetuned_rater_zero_shot'] = 0
    return dataset


def calculate_percentage_of_helpful_notes(csv_file_path):
    df = pd.read_csv(csv_file_path)
    helpful_notes_count = df[df['rating_of_note_finetuned_rater_zero_shot'] == 1].shape[0]
    total_rows = df.shape[0]
    percentage_helpful_notes = (helpful_notes_count / total_rows) * 100
    return percentage_helpful_notes



df = pd.read_csv('master.csv')
result_df = generate_prediction_for_note_finetuned(df)
#result_df = generate_prediction_for_note_finetuned_rater_finetuned(df)
result_df.to_csv('master.csv', index=False)
percentage_helpful_notes_ = calculate_percentage_of_helpful_notes('master.csv')
print(f'Percentage of helpful notes: {percentage_helpful_notes_:.2f}%')