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

tweet = "Advertisers demand billions in refunds from YouTube over skippable ads"

base_prompt = "I'm going to show you a Tweet, and I'd like you to write a brief and factual Note that provides additional context or corrects misinformation in the Tweet. Notes should be clear, concise, based on verifiable information, and useful for a wide range of readers. Here is the Tweet: '{tweet}'"

requesting_questions_and_concerns_prompt = "\n\nBefore you write the Note, I'd like you to briefly state any questions, concerns, or additional context you might want about the Tweet. After you state these concerns, you'll have the opportunity to search for sources that will help answer these concerns. Please write a few sentences or less. Only output your questions and concerns--nothing extraneous."

displaying_questions_and_concerns_prompt = "\n\nYou previously stated the following questions and concerns about the Tweet: {questions_and_concerns}"

search_query_prompt = "\n\nNow before you write a note about the tweet, you are allowed to search the internet for sources that would help you write a good note. Please respond with a short query (1-5 words), and I'll search it for you. Output only the words you'd like me to search."

displaying_sources = "\n\nTo provide additional context for your note, here are URL links to relevant sources, and summaries written by you of these sources: {sources}"
source = "URL: {url}\nSummary: {summary}\n\n"

relevant_source_prompt = "\n\nNow I'd like you to decide whether to use the following source in your note. You should only use sources which contain important information that you don't already know from other sources or common knowledge. If the text preview is an error message, say 'no.' Do you want to use the following source?\nURL: {url}\nText Preview: {text_preview}\nRespond only with 'yes' or 'no'."

summarize_source_prompt = "\n\nNow I'd like you to summarize a source which will be helpful in writing your note. Your summary should be concise. Only include information which is directly relevant for providing factual context about the Tweet, and don't include information that you already know. Here's the source.\nURL: {url}\nText: {text}"

request_final_thoughts_prompt = "\n\nDo you think the Tweet is misleading? What's misleading about it? Not every Tweet is misleading. Here's the tweet for reference: '{tweet}'"

present_final_thoughts_prompt = "\n\nWhen asked to reflect about what you'd like to discuss in your note, here's what you said: {final_thoughts}"

write_note_prompt = "\n\nNow, please write a brief and factual note to provide helpful context or correct false information for the tweet: '{tweet}'.If you make factual claims which are not common knowledge, provide your source and the full exact URL. Your key claim should be in the first sentence. Only output text which you'd like to appear in the text of the final note."


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
    return displaying_sources.format(sources=sources)


###################
###   Writer    ###
###################

questions_and_concerns = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": base_prompt.format(tweet=tweet) + requesting_questions_and_concerns_prompt}],
    max_tokens=200
).choices[0].message.content

print(questions_and_concerns)

search_query = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": base_prompt.format(tweet=tweet) + 
                                          displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                          search_query_prompt}],
    max_tokens=10
).choices[0].message.content

print(search_query)

search_results = search(search_query, num_results=10)

summaries = []
urls = []

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
            messages=[{"role": "user", "content": base_prompt.format(tweet=tweet) + 
                                                  displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                                  format_sources(summaries, urls) + 
                                                  relevant_source_prompt.format(url=url, text_preview=text_preview)}]
        ).choices[0].message.content

        print("\n" + relevance_response + "\n")

        if "yes" in relevance_response.lower():
            # Ask ChatGPT to write a brief summary
            summary = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": base_prompt.format(tweet=tweet) + 
                                                      displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                                                      format_sources(summaries, urls) + 
                                                      summarize_source_prompt.format(url=url, text=truncated_text)}]
            ).choices[0].message.content

            summaries.append(summary)
            urls.append(url)

            print(summary)

    except Exception as e:
        print(f"An error occurred with URL {url}: {e}")
    
    if len(summaries)==5:
        break


final_thoughts_prompt = (base_prompt.format(tweet=tweet) + 
                displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                format_sources(summaries, urls) + 
                request_final_thoughts_prompt.format(tweet=tweet))

final_thoughts = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": final_thoughts_prompt}],
).choices[0].message.content


final_prompt = (base_prompt.format(tweet=tweet) + 
                displaying_questions_and_concerns_prompt.format(questions_and_concerns=questions_and_concerns) + 
                format_sources(summaries, urls) + 
                present_final_thoughts_prompt.format(final_thoughts=final_thoughts) +
                write_note_prompt.format(tweet=tweet))

note = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": final_prompt}],
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
"""