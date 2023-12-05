import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm
import json
import tiktoken # for token counting
from collections import defaultdict




from dotenv import load_dotenv
load_dotenv()

df = pd.read_csv('notes_and_note_status_with_note_text.csv')
df = df.reset_index()
df_training_set = df.sample(frac=0.25)
df_testing_set = df.drop(df_training_set.index)
np.random.seed(0)
print(f"Orginal Dataset: {df.shape[0]} rows. Training Dataset: {df_training_set.shape[0]} rows. Testing Dataset: {df_testing_set.shape[0]} rows.")
df_testing_set["isNoteHelpful?"]=0
print(df_training_set)

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def create_training_file():
    with open("finetune_data.jsonl", "w") as file:
        for _, row in df_training_set.iterrows():
            tweet = row['tweet_text']
            note = row['summary']
            prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

            response = 'Yes' if row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL' else 'No'
            data = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response}
                ]
            }

            # Write the JSON object as a string in the file
            file.write(json.dumps(data) + "\n")

def test_testing_file():
    data_path = "finetune_data.jsonl"

    # Load the dataset
    with open(data_path, 'r', encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]

    # Initial dataset stats
    print("Num examples:", len(dataset))
    print("First example:")
    for message in dataset[0]["messages"]:
        print(message)


def upload_file():
    client.files.create(
    file=open("finetune_data.jsonl", "rb"),
    purpose="fine-tune"
)

def finetune():
    client.fine_tuning.jobs.create(
    training_file="file-Fig6w7YbLrwZN4cmj4GvJRes", 
    model="gpt-3.5-turbo"
)

def generate_prediction(dataset):
    for index, row in tqdm(dataset.iterrows()):
        tweet = row['tweet_text']
        note = row['summary']
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "
        response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0613:personal::8SDGR0uL",
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

ratings_df_3 = generate_prediction(df_testing_set)
to_csv(ratings_df_3)
eval = evaluate_more(ratings_df_3)
print('-'*50 + 'Evaluation' + '-'*50)
print(eval)