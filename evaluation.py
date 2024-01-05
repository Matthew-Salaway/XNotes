import pandas as pd
from sklearn.metrics import accuracy_score
import openai


ratings_1_file_path = './Data/ratings-00000.tsv'
ratings_2_file_path = './Data/ratings-00000.tsv'
note_status_history_file_path = './Data/noteStatusHistory-00000.tsv'

def rater_model_performance(api):
    
    print("To be completed. does not need a specific training set, as this is for models with no finetuning.")

    
def chatgpt_predict(prompt):
    openai.api_key = 'api-key'
    
    response = openai.Completion.create(
        engine="text-davinci-002",  # Go over this 
        prompt=prompt,
        max_tokens=100  # Go over this
    )

    lowercased_response = response.lower()

    if 'yes' in lowercased_response:
        return 'CURRENTLY_RATED_HELPFUL'
    elif 'no' in lowercased_response:
        return 'CURRENTLY_RATED_NOT_HELPFUL'
    else:
        return 'UNKNOWN_FEEDBACK'

def rater_model_performance(dataset):
    true_labels = []
    predicted_labels = []

    for _, instance in dataset.iterrows():
        tweet = instance['tweet_text']
        note = instance['summary']
        true_label = instance['currentStatus'] 
        prompt = f"I'm going to show you a Tweet and a Note about the tweet. Notes are supposed to clarify potential misinformation present in the Tweet. A helpful Note should be accurate and important. I'd like you to rate whether or not the Note is helpful. Here is the Tweet: {tweet}. Here is the Note: {note}. Do you think the Note is helpful? You must respond with only a single word: either 'Yes' or 'No.'"
        prediction = chatgpt_predict(prompt)
        true_labels.append(true_label)
        predicted_labels.append(prediction)


    accuracy = accuracy_score(true_labels, predicted_labels)
    print(f"Model Accuracy: {accuracy:.2%}")

    # Save predictions to a new CSV
    dataset['predictedStatus'] = predicted_labels
    dataset.to_csv('./Data/model_predictions.csv', index=False)





def human_rater_performance():
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



    

print(human_rater_performance())
