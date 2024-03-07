import time
import numpy as np
import pandas as pd
import concurrent.futures
from dotenv import load_dotenv
from unfurl_links import unfurl_links
from websurfer import gather_sources
from utils import call_gpt
import pdb

prompts = {
    'note': "I'm going to show you a Tweet, and I'd like you to write a helpful Community Note about it. A Community Note should correct false information or provide helpful context for a potentially misleading Tweet. Notes should be clear, concise, and based on verifiable information. The Community Notes system asks people of different political persuasions to vote on Notes, and a Note is only deemed helpful if people from across the political spectrum vote for it. Your job is to write a helpful Community Note.\nHere is the Tweet: '{tweet}'",

    'rating': "I'm going to show you a Tweet and a Community Note, and I'd like you to predict whether the Rating of the Community Note is helpful or not helpful. A Community Note should correct false information or provide helpful context for a potentially misleading Tweet. Notes should be clear, concise, and based on verifiable information. The Community Notes system asks people of different political persuasions to vote on Notes, and a Note is only deemed helpful if people from across the political spectrum vote for it. Your job is to predict whether the Community Notes system will deem the following Note helpful.\nHere is the Tweet: '{tweet}'\nHere is the Note: '{note}'",

    'initial_reflection': "\n\nFirst, I'd like you to briefly reflect on any questions, concerns, or thoughts you might have. Please write only a few sentences or less. Only output your questions and concerns--nothing extraneous.",

    'rubric_prompt': "\n\nBefore you predict the probability of the Note being rated helpful, we'll ask you a few questions about the note.",

    'rubric_list': [
        "\n\nFirst, a good note must be concise. The first sentence should immediately clarify misleading information from the original Tweet, or provide valuable context for the reader. There should be no unnecessary preamble. If you were scoring this note on a scale from 0 to 10, what score would you give its concision, and why? Explain your reasoning before providing a numerical score.",
        "\n\nSecond, a good note must be factual, accurate, and verifiable. It should make clear claims that contradict or provide context on the post. Those claims should be correct, and they should be backed up by links to sources which verify those claims. If you were scoring this note on a scale from 0 to 10, what score would you give its factuality, and why? Explain your reasoning before providing a numerical score.",
        "\n\nThird, a good note must be politically neutral. Most notes are not political at all, which is exactly how they should be. But if a note is likely to be favored by one or the other side of the political spectrum, it is unlikely to be rated helpful by people with a wide range of political views. If you were scoring this note on a scale from 0 to 10, what score would you give its political neutrality, and why? Explain your reasoning before providing a numerical score."
    ],

    'final_reflection_note_prompt': "\n\nOverall, do you think the Tweet is false or misleading? What's false or misleading about it? What additional context might you be able to add? Remember, not every Tweet is false or misleading. For reference, here's the Tweet again:\n{tweet}",
    
    'final_reflection_rating_prompt': "\n\nOverall, what are the good parts of the Note? What is it missing? On balance, do you think it's helpful? Most Notes are not helpful. A helpful note should provide brief and factual context about a potentially misleading Tweet.\nFor reference, here is the Tweet: '{tweet}'\nAnd here is the Note: '{note}'",

    'write_note_prompt': "\n\nNow, please write a brief and factual Note to provide helpful context or correct false information for the tweet. If you make factual claims which are not common knowledge, provide your source and the full exact URL. Your key claim should be in the first sentence. Only output text which you'd like to appear in the text of the final Note.",

    'write_rating_prompt': "\n\nNow, please predict the probability that the Note will be rated helpful by the Community Notes system. Output one of the following probabilities: [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]. Please output only the numerical probability that this Note will be rated helpful by the Community Notes system.",
}

def process_row(row, tagline, output_type, endpoint, links, cot, sources, rubric=False, note_column=None):
    # This function should return the updated row or any relevant data that needs to be written back to the DataFrame
    tweet = row['tweet_text']
    if output_type=="rating": note = row[note_column]
    else: note = None

    assert row['tweet_text_unfurled'] in (None, '') or pd.isna(row['tweet_text_unfurled']), f"1. {row['tweet_text_unfurled']}"
    assert row[note_column+"_unfurled"] in (None, '') or pd.isna(row[note_column+"_unfurled"]), f"2."

    if links:
        print(f"Unfurling links")
        # If there are links, read their content and present it in the text of the tweet
        if row['tweet_text_unfurled'] not in (None, '') and not pd.isna(row['tweet_text_unfurled']):
            print("This should never print, because we have nothing cached.")
            tweet = row["tweet_text_unfurled"]
        else: 
            print("entering the unfurl function first")
            tweet = unfurl_links(tweet)

            print(f"Results of unfurling links on Tweet: {tweet}")
        
        if output_type=="rating": 
            if row[note_column+"_unfurled"] not in (None, '') and not pd.isna(row[note_column+"_unfurled"]):
                print("This should never print, because we have nothing cached.")
                note = row[note_column+"_unfurled"]
            else: 
                print("entering the unfurl function first")
                note = unfurl_links(note)
                print(f"Results of unfurling links on Note: {tweet}")

        print("finished unfurling links")

    # Initialize the prompt
    if output_type=="note": prompt = prompts['note'].format(tweet=tweet)
    else: prompt = prompts['rating'].format(tweet=tweet, note=note)
    
    if cot: 
        print(f"Prompting for concerns")
        # Intiial reflection on concerns
        prompt += prompts['initial_reflection']
        initial_reflection = call_gpt(prompt, endpoint)
        prompt += f"\n\nYour Response: {initial_reflection}"
    
    if sources:
        print(f"Prompting for sources")
        sources = gather_sources(prompt, output_type, endpoint, tweet, note)
        prompt += sources
    
    if rubric:
        print(f"Prompting for rubric")
        prompt += prompts['rubric_prompt']
        for rubric_question in prompts['rubric_list']:
            prompt += rubric_question
            response = call_gpt(prompt, endpoint)
            prompt += "\nYour Response: " + response
        
    if cot: 
        # Final reflection on concerns
        if output_type=="note": prompt += prompts['final_reflection_note_prompt'].format(tweet=tweet)
        else: prompt += prompts['final_reflection_rating_prompt'].format(tweet=tweet, note=note)
        final_reflection = call_gpt(prompt, endpoint)
        prompt += f"\n\nYour Response: {final_reflection}"

    # Write note if necessary
    if output_type=="note":
        print(f"Prompting for note")
        prompt += prompts['write_note_prompt'].format(tweet=tweet)
        note = call_gpt(prompt, endpoint)
        prompt += f"\n\nYour Response: {note}"

    # Predict probability of note's helpfulness
    print(f"Prompting for rating")
    prompt += prompts['write_rating_prompt'].format(tweet=tweet, note=note)
    probability = 0
    while probability not in [0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5,
                                0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
        probability = call_gpt(prompt, endpoint, max_tokens=5)
        try: probability = float(probability)
        except: probability = 0
    prompt += f"\n\nYour Response: {probability}"

    # Store probability, prompts, and media_content in the copied row
    print(f"Updating row")
    updated_row = row.copy()
    if output_type == "note": 
        updated_row[tagline + "_note"] = note
        updated_row[tagline + "_note_probability"] = probability
        updated_row[tagline + "_prompt"] = prompt
    else:
        updated_row[tagline + "_probability"] = probability
        updated_row[tagline + "_prompt"] = prompt
    
    # Flag if the links contained images or videos
    if links:
        updated_row["tweet_text_unfurled"] = tweet
        if output_type=="rating": updated_row[note_column+"_unfurled"] = note
        media_content_flag = "WARNING: This tweet contains an image or video that cannot be displayed."
        updated_row['media_content'] = media_content_flag in prompt

    print(f"Returning updated row")
    # Return the updated row
    return updated_row



def parallel_process_df(input_path, output_type, endpoint, links, cot, sources, rubric=False, note_column=None, num_threads = 1):
    """
    Given a DataFrame which contains tweets and notes,
    and a set of options about which rater model to use,
    return a DataFrame with estimated probabilities that the notes are helpful. 
    """
    df = pd.read_csv(input_path, dtype={'noteId': str, 'tweetId': str})

    # Verify that the input DataFrame is valid
    assert 'tweet_text' in df.columns
    assert output_type in ["rating", "note"], "output_type must be rating or note"
    if output_type == "rating": 
        assert note_column is not None, "note_column must be specified for ratings"
        assert note_column in df.columns, f"note_column {note_column} not in df.columns"
    else:
        assert rubric == False, "rubric must be False for notes"

    # Generate column name for the outputs
    tagline = f"{output_type}"
    if output_type=="rating": tagline += f"_{note_column}"
    tagline += f"_{endpoint}"
    if links is True: tagline += f"_links"
    if cot is True: tagline += f"_cot"
    if sources is True: tagline += f"_sources"
    if rubric is True: tagline += f"_rubric"

    # Example tagline: "rating_gpt-3.5_links_cot_rubric" -- uses everything but sources

    # Initialize columns to store outputs
    if output_type=="note" and f"{tagline}_prompt" not in df.columns:
        df[f"{tagline}_note"] = ''
        df[f"{tagline}_note_probability"] = np.NaN
        df[f"{tagline}_prompt"] = ''
    elif output_type=="rating" and f"{tagline}_prompt" not in df.columns:
        df[f"{tagline}_probability"] = np.NaN
        df[f"{tagline}_prompt"] = ''
    if links==True:
        if "tweet_text_unfurled" not in df.columns: df["tweet_text_unfurled"] = ""
        if output_type=="rating" and f"{note_column}_unfurled" not in df.columns: df[f"{note_column}_unfurled"] = ""
        if 'media_content' not in df.columns: df['media_content'] = ''

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_to_idx = {}
        for idx, row in df.iterrows():
            if idx < 191: continue
            # Check if the row is already processed
            if row[f"{tagline}_prompt"] in (None, '', np.nan):
                print(f"Row {idx} will be processed.")
                # Submit only unprocessed rows
                future = executor.submit(process_row, row, tagline, output_type, endpoint, links, cot, sources, rubric, note_column)
                future_to_idx[future] = idx
            else: 
                print(f"Row {idx} already processed.")

        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                # Get the result from the future and update the DataFrame
                result = future.result()
                print(f"Row {idx} processed successfully.")
                print(result)
                df.loc[idx] = result
                df.to_csv(input_path, index=False)


            except Exception as exc:
                print(f'Row {idx} generated an exception: {exc}')

    return None

if __name__=="__main__":
    parallel_process_df(
        input_path = "Data/master.csv",
        output_type='rating',
        endpoint='gpt-3.5-turbo-1106',
        links=True,
        cot=False,
        sources=False,
        rubric=False,
        note_column='original_note',
        num_threads=1
    )

    parallel_process_df(
        input_path = "Data/master.csv",
        output_type='rating',
        endpoint='gpt-3.5-turbo-1106',
        links=True,
        cot=False,
        sources=False,
        rubric=True,
        note_column='original_note',
        num_threads=256
    )

