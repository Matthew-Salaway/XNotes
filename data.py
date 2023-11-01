# Download the files from the following link and save them in the Data folder
# https://twitter.com/i/communitynotes/download-data
# The files are named as follows: Notes data (1), Ratings data (1 & 2), Note status history data (1)

# From these files, make a new data frame with the nessary columns for training the Rater model.

# Make a function that uses pandas to import the files in the the Data folder
# and returns a data frame with the necessary columns for training the model.

import pandas as pd

notes_file_path = './Data/notes-00000.tsv'
ratings_1_file_path = './Data/ratings-00000.tsv'
ratings_2_file_path = './Data/ratings-00000.tsv'
note_status_history_file_path = './Data/noteStatusHistory-00000.tsv'
user_enrollment_file_path = './Data/userEnrollment-00000.tsv'



def import_and_combine_data_Rater_Model(necessary_columns):

    notes_df = pd.read_csv(notes_file_path, sep='\t', usecols=necessary_columns)

notes_df = pd.read_csv(notes_file_path, sep='\t', usecols=['noteId', 'tweetId', 'summary'])
note_status_df = pd.read_csv(note_status_history_file_path, sep='\t', usecols=['noteId', 'currentStatus'])

result = pd.merge(notes_df[['noteId', 'tweetId', 'summary']], note_status_df[['noteId', 'currentStatus']], on='noteId')

print(result.head())
print(result.columns)
print(result.shape)
print(result.iloc[1])

# Use twitter API to get the tweet text from the tweetId column
