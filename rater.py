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

def append_results_to_master(col_title, results_df, note_id_df):
    """
    Appends the results of the note rating to the master.csv in a new column called col_title
    """
    master_csv_path = "../Data/master.csv"
    
    # Read the master CSV file into a DataFrame
    master_df = pd.read_csv(master_csv_path)

    # Merge the noteID DataFrame with the results DataFrame based on index
    # Assuming the first (and only) column in results_df contains the results
    combined_results_df = note_id_df.join(results_df)

    # Merge the master DataFrame with the combined results DataFrame based on the noteID
    # Assuming 'noteID' is the column in note_id_df and master_df for matching
    merged_df = pd.merge(master_df, combined_results_df, how='left', left_on='noteID', right_index=True)

    # Rename the results column
    # Assuming the first (and only) column in results_df contains the results
    result_column_name = results_df.columns[0]
    merged_df.rename(columns={result_column_name: col_title}, inplace=True)

    merged_df.to_csv("../Data.master.csv", index=False)



def evaluate(current_statuses_df, predicted_statuses_df):
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


if __name__=="__main__":
    # Get the tweets, notes, and model into generate. Take output and evaluate agaonst the actual. append these results to master
    df = pd.read_csv('master.csv')
    tweets = df['tweet_text']
    notes = df['original_note']
    model="gpt-4-1106-preview",
    results_df = generate_prediction(tweets, notes, model)
    evaluate(df["currentStatus"], results_df)
    append_results_to_master("zero_shot_gpt_4_turbo", results_df, df["noteID"])

