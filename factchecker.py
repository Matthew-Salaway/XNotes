import pandas as pd
from dotenv import load_dotenv
from unfurl_links import unfurl_links
from websurfer import gather_sources
from utils import call_gpt
import numpy as np
import pdb
import time

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

def process_df(input_path, output_type, endpoint, links, cot, sources, rubric=False, note_column=None):
    """
    Given a DataFrame which contains tweets and notes,
    and a set of options about which rater model to use,
    return a DataFrame with estimated probabilities that the notes are helpful. 
    """
    df = pd.read_csv(input_path, doutput_type={'noteId': str, 'tweetId': str})
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
    if output_type=="note" and f"{tagline}_note" not in df.columns:
        df[f"{tagline}_note"] = ''
        df[f"{tagline}_note_probability"] = np.NaN
        df[f"{tagline}_prompt"] = ''
    elif output_type=="rating" and f"{tagline}_rating" not in df.columns:
        df[f"{tagline}_probability"] = np.NaN
        df[f"{tagline}_prompt"] = ''
    if links==True and 'media_content' not in df.columns: df['media_content'] = ''

    for idx, row in df.iterrows():
        print(f"Processing row {idx} of {len(df)}")
        # Skip if already completed
        if row[f"{tagline}_prompt"] != '': 
            print(row[f"{tagline}_prompt"])
            continue

        tweet = row['tweet_text']
        if output_type=="rating": 
            note = row[note_column]
        else: note = None

        prompt = prompts['rating'].format(tweet=tweet, note=note)

        # Start timing. I want to see how long each piece takes. 
        start = time.time()

        if links:
            # If there are links, read their content and present it in the text of the tweet
            tweet = unfurl_links(tweet)
            if output_type=="rating": note = unfurl_links(note)

            print("Links finished in {:.2f} seconds.\n".format(time.time()-start))
            start = time.time()
        
        if cot: 
            # Intiial reflection on concerns
            prompt += prompts['initial_reflection']
            initial_reflection = call_gpt(prompt, endpoint)
            prompt += f"\n\nYour Response: {initial_reflection}"

            print("COT finished in {:.2f} seconds.\n".format(time.time()-start))
            start = time.time()
        
        if sources:
            sources = gather_sources(prompt, output_type, endpoint, tweet, note)
            prompt += sources
            
            print("Sources finished in {:.2f} seconds.\n".format(time.time()-start))
            start = time.time()
        
        if rubric:
            prompt += prompts['rubric_prompt']
            for rubric_question in prompts['rubric_list']:
                prompt += rubric_question
                response = call_gpt(prompt, endpoint)
                prompt += "\nYour Response: " + response
            
            print("Rubric finished in {:.2f} seconds.\n".format(time.time()-start))
            start = time.time()
            
        if cot: 
            # Final reflection on concerns
            if output_type=="note": prompt += prompts['final_reflection_note_prompt'].format(tweet=tweet)
            else: prompt += prompts['final_reflection_rating_prompt'].format(tweet=tweet, note=note)
            final_reflection = call_gpt(prompt, endpoint)
            prompt += f"\n\nYour Response: {final_reflection}"

            print("COT finished in {:.2f} seconds.\n".format(time.time()-start))
            start = time.time()

        # Write note if necessary
        if output_type=="note":
            prompt += prompts['write_note_prompt'].format(tweet=tweet)
            note = call_gpt(prompt, endpoint)
            prompt += f"\n\nYour Response: {note}"

        # Predict probability of note's helpfulness
        prompt += prompts['write_rating_prompt'].format(tweet=tweet, note=note)
        probability = call_gpt(prompt, endpoint, max_tokens=50)
        prompt += f"\n\nYour Response: {probability}"

        # Store probability, prompts, and media_content in df
        if output_type=="note": 
            df.loc[idx, tagline + "_note"] = note
            df.loc[idx, tagline + "_note_probability"] = probability
            df.loc[idx, tagline + "_prompt"] = prompt
        else:
            df.loc[idx, tagline + "_probability"] = probability
            df.loc[idx, tagline + "_prompt"] = prompt
            
        # Flag if the links contained images or videos
        if links==True:
            media_content_flag = "WARNING: This tweet contains an image or video that cannot be displayed."
            if media_content_flag in prompt:
                media_content = True
            else: media_content = False
            df.loc[idx, 'media_content'] = media_content

        # Save df
        df.to_csv(input_path, index=False)

        print("Final outputs and saving finished in {:.2f} seconds.\n".format(time.time()-start))

        print(f"\n\n##################\nFinished row {idx} of {len(df)}\n##############\n")
        print(f"Prompt: {prompt}\n\n")
        if output_type=="note": print(f"Note: {note}\n\n")
        print(f"Probability: {probability}\n\n")
        if links==True: print(f"Media Content: {media_content}\n\n")

    return None



if __name__=="__main__":
    process_df(
        input_path = "Data/master.csv",
        output_type='rating',
        endpoint='gpt-3.5-turbo-1106',
        links=True, 
        cot=True, 
        sources=True, 
        rubric=True, 
        note_column='original_note',
    )

