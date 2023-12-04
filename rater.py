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

def generate_prediction_2(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['summary']
        prompt = f"Your task is to assess the helpfulness of a Note that aims to clarify potential misinformation in a Tweet. To be considered 'helpful,' a Note should be factually accurate, directly relevant to the Tweet's content, and important for understanding the context. Below is the Tweet in question: {tweet}. Accompanying it is the Note designed to address its contents: {note}. Based on these criteria, do you find the Note to be helpful in clarifying the Tweet? Respond with either \"Yes\" or \"No\""


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

def generate_prediction_3(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['summary']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? Think step by step. You must respond with only a single word: either \"Yes\" or \"No\" "

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

def evaluate_more(dataset):
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    for index, row in dataset.iterrows():
        if row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL' and row['isNoteHelpful?']==1:
            tp += 1
        elif row['currentStatus'] == 'CURRENTLY_RATED_NOT_HELPFUL' and row['isNoteHelpful?']==0:
            tn += 1
        elif row['currentStatus'] == 'CURRENTLY_RATED_NOT_HELPFUL' and row['isNoteHelpful?']==1:
            fp += 1
        elif row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL' and row['isNoteHelpful?']==0:
            fn += 1
        

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    specificity = tn / (tn + fp)
    f1 = 2 * precision * recall / (precision + recall)

    return {'Accuracy': accuracy, 'Precision': precision, 'Recall': recall, 'Specificity': specificity, 'F1': f1}


# Prompt 1
# ratings_df = generate_prediction(df)
# to_csv(ratings_df)
# accuracy = evaluate(ratings_df)
# print('-'*50 + 'Accuracy' + '-'*50)
# print(accuracy)
# eval = evaluate_more(ratings_df)
# print('-'*50 + 'Evaluatiion' + '-'*50)
# print(eval)
# Accuracy: 71.91%
# {'Accuracy': 0.702054794520548, 'Precision': 0.632183908045977, 'Recall': 0.8270676691729323, 'Specificity': 0.5974842767295597, 'F1': 0.7166123778501629}
# GPT-4 turbo analysis: {'Accuracy': 0.8321917808219178, 'Precision': 0.75, 'Recall': 0.9473684210526315, 'Specificity': 0.7358490566037735, 'F1': 0.8372093023255814}

# Prompt 2
# ratings_df_2 = generate_prediction_2(df)
# to_csv(ratings_df_2)
# eval = evaluate_more(ratings_df_2)
# print('-'*50 + 'Evaluation' + '-'*50)
# print(eval)
# Accuracy: 69.17%
# {'Accuracy': 0.6472602739726028, 'Precision': 0.5669642857142857, 'Recall': 0.9548872180451128, 'Specificity': 0.389937106918239, 'F1': 0.711484593837535}

# Prompt 3
# ratings_df_3 = generate_prediction_3(df)
# to_csv(ratings_df_3)
# eval = evaluate_more(ratings_df_3)
# print('-'*50 + 'Evaluation' + '-'*50)
# print(eval)
# {'Accuracy': 0.7054794520547946, 'Precision': 0.6459627329192547, 'Recall': 0.7819548872180451, 'Specificity': 0.6415094339622641, 'F1': 0.707482993197279}
# GPT-4 turbo analysis: {'Accuracy': 0.8287671232876712, 'Precision': 0.7515151515151515, 'Recall': 0.9323308270676691, 'Specificity': 0.7421383647798742, 'F1': 0.8322147651006712}
# GPT-4 analysis: {'Accuracy': 0.7431506849315068, 'Precision': 0.6666666666666666, 'Recall': 0.8721804511278195, 'Specificity': 0.6352201257861635, 'F1': 0.7557003257328989}

