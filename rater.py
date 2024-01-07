import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm

from dotenv import load_dotenv

def generate_prediction(tweets, notes, model_endpoint):
    """
    Given a list of tweets and notes, the model predicts the rating for each note
    based on the prompt and model_endpoint and returns the predictions as a dataframe.
    """
    assert len(tweets) == len(notes), "DataFrames must be of the same size"

    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    dotenv_path = Path('/Users/adityajadhav/Downloads/Rater/notes.env')
    load_dotenv(dotenv_path=dotenv_path)


    results = pd.DataFrame(columns=['results'])

    for tweet, note in tqdm(zip(tweets, notes), desc="Processing", total=len(tweets)):
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: '''{tweet}'''. Here is the Note: '''{note}'''. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

        response = client.chat.completions.create(
        model=model_endpoint,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2
        )
        
        if response.choices[0].message.content == 'Yes':
            results = results.append(1)
        else:
            results = results.append(0)
    return results

def append_results_to_master(col_title, results, note_ids):
    """
    Appends the results of the note rating to the master.csv in a new column called col_title
    """
    # Iterate through the results, find the row with same note_id, put result in that row and col_title



def evaluate(current_statuses, predicted_statuses):
    """
    Prints evaluation metrics on the predicted rating and actual rating of the note. 
    """
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


# GPT Tubro Model Name: gpt-4-1106-preview

if __name__=="__main__":
    # Get the tweets, notes, and model into generate. Take output and evaluate agaonst the actual. append these results to master
    df = pd.read_csv('master.csv')
    tweets = df['tweet_text']
    notes = df['original_note']
    model="gpt-4-1106-preview",

    # ratings_df = generate_prediction(df)
    # to_csv(ratings_df)
    # accuracy = evaluate(ratings_df)
    # print('-'*50 + 'Accuracy' + '-'*50)
    # print(accuracy)
    # eval = evaluate_more(ratings_df)
    # print('-'*50 + 'Evaluatiion' + '-'*50)
    # print(eval)
    # Accuracy: 71.91%
