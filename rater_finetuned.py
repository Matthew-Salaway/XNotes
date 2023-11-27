import pandas as pd
import numpy as np
import openai
from openai import OpenAI
import os
from pathlib import Path
from tqdm import tqdm

from dotenv import load_dotenv
load_dotenv()

df = pd.read_csv('notes_and_note_status_with_note_text.csv')
df = df.reset_index()
df_training_set = df.sample(frac=0.2)
df_testing_set = df.drop(df_training_set.index)
print(f"Orginal Dataset: {df.shape[0]} rows. Training Dataset: {df_training_set.shape[0]} rows. Testing Dataset: {df_testing_set.shape[0]} rows.")
df_testing_set["isNoteHelpful?"]=0
print(df_testing_set)

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


