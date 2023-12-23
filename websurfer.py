import openai
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')


###################
###   Prompts   ###
###################

tweet = "Many people have been asking me how I got myocarditis despite being unvaccinated. Two days after spending time with a friend who had just received the vaccine, my heart began to have severe irregularities, and it took me a year to recover. Vaccine shedding is a valid concern."

note_prompt = "I'm going to show you a Tweet, and I'd like you to write a brief and factual Community Note that provides additional context or corrects misinformation in the Tweet. Notes should be clear, concise, based on verifiable information, and useful for a wide range of readers.\nHere is the Tweet: '{tweet}'"

rating_prompt = "I'm going to show you a Tweet and a Community Note, and I'd like you to provide a Rating of whether the Note is helpful or not helpful. A helpful Note should briefly and factually provide helpful context for a potentially misleading Tweet.\nHere is the Tweet: '{tweet}'\nHere is the Note: '{note}'"

requesting_questions_and_concerns_prompt = "\n\nBefore you write the {type}, I'd like you to briefly state any questions, concerns, or additional context you might want about the Tweet. After you state these concerns, you'll have the opportunity to search for sources that will help answer these concerns. Please write a few sentences or less. Only output your questions and concerns--nothing extraneous."

displaying_questions_and_concerns_prompt = "\n\nYou previously stated the following questions and concerns about the Tweet: {questions_and_concerns}"

search_query_prompt = "\n\nNow before you write the {type} about the tweet, you are allowed to search the internet for sources that would help you write a good {type}. Please respond with a short query (1-5 words), and I'll search it for you. Output only the words you'd like me to search."

displaying_sources = "\n\nTo provide additional context for your {type}, here are URL links to relevant sources, and summaries written by you of these sources: {sources}"

source = "URL: {url}\nSummary: {summary}\n\n"

relevant_source_prompt = "\n\nNow I'd like you to decide whether to use the following source in your {type}. You should only use sources which contain important information that you don't already know from other sources or common knowledge. If the text preview is an error message, say 'no.' Do you want to use the following source?\nURL: {url}\nText Preview: {text_preview}\nRespond only with 'yes' or 'no'."

summarize_source_prompt = "\n\nNow I'd like you to summarize a source which will be helpful in writing your {type}. Your summary should be concise. Only include information which is directly relevant for providing useful factual context, and don't include information that you already know. Here's the source.\nURL: {url}\nText: {text}"

request_final_note_thoughts_prompt = "\n\nOverall, do you think the Tweet is misleading? What's misleading about it? Not every Tweet is misleading. Here's the tweet for reference: '{tweet}'"

request_final_rating_thoughts_prompt = "\n\nOverall, what are the good parts of the Note? What is it missing? On balance, do you think it's helpful? Most Notes are not helpful. A helpful note should provide brief and factual context about a potentially misleading Tweet.\nFor reference, here is the Tweet: '{tweet}'\nAnd here is the Note: '{note}'"

present_final_thoughts_prompt = "\n\nWhen asked to reflect about the key considerations for your {type}, here's what you said: {final_thoughts}"

write_note_prompt = "\n\nNow, please write a brief and factual Note to provide helpful context or correct false information for the tweet: '{tweet}'.If you make factual claims which are not common knowledge, provide your source and the full exact URL. Your key claim should be in the first sentence. Only output text which you'd like to appear in the text of the final Note."

write_rating_prompt = "\n\nNow, please decide whether the Note is helpful or not helpful.\nFor reference, here is the Tweet: '{tweet}'\nAnd here is the Note: '{note}'\nPlease output only 'Helpful.' or 'Not helpful."


###################
###    Utils    ###
###################

def truncate_text(text, max_tokens):
    tokens = text.split()
    if len(tokens) <= max_tokens:
        return text  
    return ' '.join(tokens[:max_tokens])

def format_sources(summaries, urls):
    if len(summaries)==0: return ""
    sources = ""
    for s, u in zip(summaries, urls):
        sources += source.format(url=u, summary=s)
    return displaying_sources.format(sources=sources, type=type)

def call_gpt(prompt, endpoint, max_tokens):
    return openai.chat.completions.create(
        model=endpoint,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens
    ).choices[0].message.content


###################
###   Writer    ###
###################

def main(type, endpoint, tweet, note=None):
    assert type.lower() in ["rating", "note"], "type must be Rating or Note"

    # Format base prompt
    base_prompt = note_prompt if type.lower()=="note" else rating_prompt
    base_prompt = base_prompt.format(tweet=tweet, note=note)

    # Ask GPT for initial questions and concerns
    questions_and_concerns = openai.chat.completions.create(
        model=endpoint,
        messages=[{"role": "user", "content": base_prompt + requesting_questions_and_concerns_prompt.format(type=type)}],
        max_tokens=200
    ).choices[0].message.content

    print(questions_and_concerns)

    # Generate a search query
    search_query = openai.chat.completions.create(
        model=endpoint,
        messages=[{"role": "user", "content": note_prompt.format(tweet=tweet) + 
                                            displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                            search_query_prompt.format(type=type)}],
        max_tokens=10
    ).choices[0].message.content

    print(search_query)

    # Search the query
    search_results = search(search_query, num_results=10)

    # Loop through search results to summarize relevant sources
    summaries, urls = [], []
    for url in search_results:
        print(url)
        try:
            # Fetch the text from the URL
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            truncated_text = truncate_text(text, max_tokens=3000)
            text_preview = truncate_text(text, max_tokens=500)
            
            print(text_preview)

            # Interact with ChatGPT to check if the source is useful and necessary
            relevance_response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": note_prompt.format(tweet=tweet) + 
                                                    displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                                    format_sources(summaries, urls) + 
                                                    relevant_source_prompt.format(url=url, text_preview=text_preview, type=type)}]
            ).choices[0].message.content

            print("\n" + relevance_response + "\n")

            if "yes" in relevance_response.lower():
                # Ask ChatGPT to write a brief summary
                summary = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": note_prompt.format(tweet=tweet) + 
                                                        displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                                        format_sources(summaries, urls) + 
                                                        summarize_source_prompt.format(url=url, text=truncated_text, type=type)}]
                ).choices[0].message.content

                summaries.append(summary)
                urls.append(url)

                print(summary)

        except Exception as e:
            print(f"An error occurred with URL {url}: {e}")
        
        if len(summaries)==5:
            break

    # After summarizing relevant sources, ask the model to reflect on its final thoughts
    if type.lower()=="note": final_thoughts_prompt = request_final_note_thoughts_prompt.format(tweet=tweet, type=type)
    else: final_thoughts_prompt = request_final_rating_thoughts_prompt.format(tweet=tweet, type=type)

    final_thoughts = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": base_prompt.format(note=note, tweet=tweet) +
                                              displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                              format_sources(summaries, urls) + 
                                              final_thoughts_prompt}],
    ).choices[0].message.content

    # Prompt model for a final answer
    if type.lower()=="note": final_prompt = write_note_prompt.format(tweet=tweet)
    else: final_prompt = write_note_prompt.format(tweet=tweet, note=note)
    note = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": (base_prompt.format(tweet=tweet, type=type) + 
                                              displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                              format_sources(summaries, urls) + 
                                              present_final_thoughts_prompt.format(final_thoughts=final_thoughts, type=type) +
                                              final_prompt)}],
    ).choices[0].message.content

    print()
    print(final_prompt)
    print()
    print(note)

    """
    Here's the flow of how this file should work:

    Tweet --> Prompt
    Prompt --> Search Query
    Search Query --> Results
    Results --> Choose N Results
    N Results --> N Summaries
    N Summaries --> Add to original prompt
    Return prompt

    It should work for both the note writer and the rater. 


    TODO:
    Check whether this works. Run it for both raters and writers. Read all the prompts and make sure they're accurate. Check it with GPT. 
    Run this for all tweets and all human notes. Use that process to modularize the code. 
    Evaluate the results of both of those. Maybe decide the final column names for master.csv. 



    Priorities
    1. Identifying which tweets require notes. 
        We need simple filters at the beginning, from low to high cost. 
        At the end of the note writing process, we should check whether a note is still necessary. 
    2. Identifying which of the notes are highest quality. 
        We only want to post the really good ones. But this has to be an automatic process. Incredibly high precision. 
    3. Getting Grok. Elon will not like if I publish this with ChatGPT. Simple man, simple motivations. Contact Jay Baxter -- when?
    4. Think about deployment options
    - Tweetbot. It would make a lot of mistakes. It would be a lot of work to maintain on a technical backend upkeep level. This makes the project inherently longer term. 
    - Become a Top Contributor. That would be based. Then release the code and a paper explaining how we did it. 


    """