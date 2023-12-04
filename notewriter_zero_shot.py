import pandas as pd
import numpy as np
import openai
import os
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv


load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key


df = pd.read_csv('master.csv')

def note_writer_zero_shot(dataset):
    for index, row in tqdm(dataset.iterrows(), total=len(dataset)):
        tweet = row['tweet_text']
        prompt = f"I'm going to show you a Tweet and I would like you to make a note for this tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to create a Note based on a Tweet. Here is the Tweet: {tweet}."

        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100
        )

        model_response = response['choices'][0]['message']['content']
        dataset.at[index, 'note_zero_shot'] = model_response 

    return dataset

df = pd.read_csv('master.csv')
result_df = note_writer_zero_shot(df)
result_df.to_csv('master.csv', index=False)


