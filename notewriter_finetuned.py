import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv
import json
import tiktoken  # for token counting
from collections import defaultdict

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


df = pd.read_csv('helpful_notes.csv')
df = df.reset_index()
df_training_set = df
#df_testing_set = df.drop(df_training_set.index)
#np.random.seed(0)
#print(
 #   f"Orginal Dataset: {df.shape[0]} rows. Training Dataset: {df_training_set.shape[0]} rows. Testing Dataset: {df_testing_set.shape[0]} rows.")
#df_testing_set["isNoteHelpful?"] = 0
#print(df_training_set)


def create_training_file():
    with open("latest_finetune_data.jsonl", "w") as file:
        for _, row in df_training_set.iterrows():
            tweet = row['tweet_text']
            prompt = f"I'm going to show you a Tweet and I would like you to make a note for this tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to create a Note based on a Tweet. Here is the Tweet: {tweet}. Make sure that the note is less than 100 words."
            note = row['original_note']
            data = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": note}
                ]
            }
            file.write(json.dumps(data) + "\n")


def create_helpful_csv(original_csv_path):
    df_master = pd.read_csv('master.csv')
    columns_to_include = ['noteId', 'tweetId', 'original_note', 'tweet_text']

    new_df = pd.DataFrame(columns=columns_to_include)

    for index, row in df_master.iterrows():
        if row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL':
            new_row = row[columns_to_include]
            new_df = new_df.append(new_row, ignore_index=True)
    new_df.to_csv('helpful_notes.csv', index=False)


def note_writer_finetuned(dataset):
    for index, row in tqdm(dataset.iterrows(), total=len(dataset)):
        tweet = row['tweet_text']
        prompt = f"I'm going to show you a Tweet and I would like you to make a note for this tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to create a Note based on a Tweet. Here is the Tweet: {tweet}. Make sure that the note is less than 100 words."

        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0613:personal::8WijoRJq",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )

        model_response = response.choices[0].message.content
        dataset.at[index, 'note_finetuned'] = model_response
    return dataset



#create_training_file()

#response = client.files.create(
 #   file=open("latest_finetune_data.jsonl", "rb"),
  #  purpose="fine-tune"
#)
#print(response)

#file_id = "file-9QwNlbVxxcFIw8UUCIJKhSgz"
#response = client.fine_tuning.jobs.create(
 #  training_file=file_id,
  #model="gpt-3.5-turbo"
#)

#print(response)

#print(client.fine_tuning.jobs.list_events(fine_tuning_job_id="ftjob-aoLNywg7cgMKfLaB8Saga8kF", limit=10))
#print(client.fine_tuning.jobs.retrieve("ftjob-1rrNjYaCBYhgFMjcXDVJgs9k"))




df = pd.read_csv('master.csv')
result_df = note_writer_finetuned(df)
result_df.to_csv('master.csv', index=False)
