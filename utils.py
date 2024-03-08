import pandas as pd
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')

def call_gpt(prompt, endpoint, max_tokens=200):
    return openai.chat.completions.create(
        model=endpoint,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    ).choices[0].message.content


def truncate_text(text, max_tokens):
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text  
    return ' '.join(tokens[:max_tokens])


def human_rater_performance():
    """
    Evaluates the agreement between different human raters in classifying notes as helpful or not. 
    It compares user ratings from two files with the current status of notes to calculate 
    metrics like accuracy, precision, recall, specificity, and F1 score of user ratings.
    """

    ratings_1_file_path = './Data/ratings-00000.tsv'
    ratings_2_file_path = './Data/ratings-00000.tsv'
    note_status_history_file_path = './Data/noteStatusHistory-00000.tsv'

    rating_1_df = pd.read_csv(ratings_1_file_path, sep='\t', usecols=['noteId', 'helpfulnessLevel'])
    rating_2_df = pd.read_csv(ratings_2_file_path, sep='\t', usecols=['noteId', 'helpfulnessLevel'])
    note_status_df = pd.read_csv(note_status_history_file_path, sep='\t', usecols=['noteId', 'currentStatus'])

    # Map note id to the current status. 0 if not helpful, 1 if helpful
    note_id_to_status = {}
    for i, row in note_status_df.iterrows():
        if row['currentStatus'] == 'CURRENTLY_RATED_NOT_HELPFUL':
            note_id_to_status[row['noteId']] = 0
        elif row['currentStatus'] == 'CURRENTLY_RATED_HELPFUL':
            note_id_to_status[row['noteId']] = 1
    
    print(note_id_to_status)


    # iterate through all user ratings. if they have a note in the map see if its wrong or right
    tp = 0
    fp = 0
    tn = 0
    fn = 0
    for i, row in rating_1_df.iterrows():
        if row['noteId'] in note_id_to_status:
            is_currently_helpful = note_id_to_status[row['noteId']]
            if is_currently_helpful:
                if row['helpfulnessLevel'] == 'HELPFUL':
                    tp += 1
                else:
                    fn += 1
            else:
                if row['helpfulnessLevel'] == 'HELPFUL':
                    fp += 1
                else:
                    tn += 1
    print(tp, fp, tn, fn)

    accuracy = (tp + tn) / (tp + tn + fp + fn)
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    specificity = tn / (tn + fp)
    f1 = 2 * precision * recall / (precision + recall)

    return {'Accuracy': accuracy, 'Precision': precision, 'Recall': recall, 'Specificity': specificity, 'F1': f1}