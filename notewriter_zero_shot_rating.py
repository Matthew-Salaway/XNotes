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


def generate_prediction_for_note_zeroshot(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['note_zero_shot']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )

        if response.choices[0].message.content == 'Yes':
            dataset.at[index,'isNoteHelpful?'] = 1
        else:
            dataset.at[index,'isNoteHelpful?'] = 0
    return dataset

def generate_prediction_for_note_zeroshot_2(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['note_zero_shot']
        prompt = f"Your task is to assess the helpfulness of a Note that aims to clarify potential misinformation in a Tweet. To be considered 'helpful,' a Note should be factually accurate, directly relevant to the Tweet's content, and important for understanding the context. Below is the Tweet in question: {tweet}. Accompanying it is the Note designed to address its contents: {note}. Based on these criteria, do you find the Note to be helpful in clarifying the Tweet? Respond with either \"Yes\" or \"No\""
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )

        if response.choices[0].message.content == 'Yes':
            dataset.at[index,'isNoteHelpful?'] = 1
        else:
            dataset.at[index,'isNoteHelpful?'] = 0
    return dataset


def generate_prediction_for_note_zeroshot_3(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['note_zero_shot']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? Think step by step. You must respond with only a single word: either \"Yes\" or \"No\" "
        response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )

        if response.choices[0].message.content == 'Yes':
            dataset.at[index,'isNoteHelpful?'] = 1
        else:
            dataset.at[index,'isNoteHelpful?'] = 0
    return dataset

def calculate_percentage_of_helpful_notes(csv_file_path):
   
    df = pd.read_csv(csv_file_path)

  
    helpful_notes_count = df[df['isNoteHelpful?'] == 1].shape[0]

    total_rows = df.shape[0]
    percentage_helpful_notes = (helpful_notes_count / total_rows) * 100

    return percentage_helpful_notes



df = pd.read_csv('master.csv')
#result_df_1 = generate_prediction_for_note_zeroshot(df)
#result_df_1.to_csv('prompt_1_master.csv', index=False)
percentage_helpful_notes_1 = calculate_percentage_of_helpful_notes('prompt_1_master.csv')  #Prompt 1: Percentage of helpful notes: 96.23%

#result_df_2 = generate_prediction_for_note_zeroshot_2(df)
#result_df_2.to_csv('prompt_2_master.csv', index=False)
percentage_helpful_notes_2 = calculate_percentage_of_helpful_notes('prompt_2_master.csv') # Prompt 2: Percentage of helpful notes: 97.95%

#result_df_3 = generate_prediction_for_note_zeroshot_3(df)
#result_df_3.to_csv('prompt_3_master.csv', index=False)
percentage_helpful_notes_3 = calculate_percentage_of_helpful_notes('prompt_3_master.csv') #  Prompt 3: Percentage of helpful notes: 94.52%



print(f' Prompt 1: Percentage of helpful notes: {percentage_helpful_notes_1:.2f}%') #Prompt to be used for the rest of the project
#print(f' Prompt 2: Percentage of helpful notes: {percentage_helpful_notes_2:.2f}%')
#print(f' Prompt 3: Percentage of helpful notes: {percentage_helpful_notes_3:.2f}%')








