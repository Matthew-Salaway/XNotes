###########
# Writer # 
###########

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




#########
# Rater # 
#########

def create_fine_tuning_file(tweets, notes, current_statuses, file_name):
    """
    Creates a .jsonl file for fine-tuning a language model. Takes three lists as input: 
    'tweets', 'notes', and 'current_statuses'. Each element in these lists corresponds to 
    one training example. Each line in the .jsonl file represents a dialogue interaction with 
    a prompt based on the tweet and note, and a response indicating if the note is helpful.
    """

    with open(file_name, "w") as file:
        for tweet, note, status in zip(tweets, notes, current_statuses):
            
            prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either \"Yes\" or \"No\" "

            response = 'Yes' if status == 'CURRENTLY_RATED_HELPFUL' else 'No'
            data = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": response}
                ]
            }

            # Write the JSON object as a string in the file
            file.write(json.dumps(data) + "\n")

def test_fine_tuning_file(file_name):
    """
    Ensures the fine-tuning file is formated properly.
    """

    data_path = file_name

    # Load the dataset
    with open(data_path, 'r', encoding='utf-8') as f:
        dataset = [json.loads(line) for line in f]

    # Initial dataset stats
    print("Num examples:", len(dataset))
    print("First example:")
    for message in dataset[0]["messages"]:
        print(message)


def upload_file(file_name):
    """
    Uploads the fine-tuning file to OpenAI.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    client.files.create(
    file=open(file_name, "rb"),
    purpose="fine-tune"
)

def finetune(model, training_file_key):
    """
    Begins fine-tuning process with specified model and training file key.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)
    client.fine_tuning.jobs.create(
    training_file=training_file_key, 
    model=model
)

