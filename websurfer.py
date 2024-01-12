import openai
from googlesearch import search
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
from utils import call_gpt, truncate_text
import pdb

load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_KEY')

prompts = {
    'search_query_prompt': "\n\nNow before you write the {output_type} about the tweet, you are allowed to search the internet for sources that would help you write a good {output_type}. Please respond with a short query (1-5 words), and I'll search it for you. Output only the words you'd like me to search.",
    'displaying_sources_prompt': "\n\nTo provide additional context for your {output_type}, here are some sources. If you use information from a source to write a Note, remember to cite the exact URL. Here are URLs and summaries of the sources written by you. {sources}",
    'source_prompt': "\n\nURL: {url}\nSummary: {summary}",
    'relevant_source_prompt': "\n\nNow I'd like you to decide whether to use the following source in your {output_type}. You should only use sources which contain important information that you don't already know from other sources or common knowledge. You'll only get three sources. If the text preview is an error message, say 'no.' Do you want to use the following source?\nURL: {url}\nText Preview: {text_preview}\nRespond only with 'yes' or 'no'.",
    'summarize_source_prompt': "\n\nNow I'd like you to summarize a source which will be helpful in writing your {output_type}. Your summary should be concise. Only include information which is directly relevant for providing useful factual context, and don't include information that you already know. Consider using direct quotes from the source. Here's the source.\nURL: {url}\nText: {text}"
}

def format_sources(summaries, urls):
    if len(summaries)==0: return ""
    sources = ""
    for s, u in zip(summaries, urls):
        sources += prompts['source_prompt'].format(url=u, summary=s)
    return prompts['displaying_sources_prompt'].format(sources=sources, output_type=output_type)


def gather_sources(prompt, output_type, endpoint, tweet, note=None, num_sources=3):
    """
    Given a prompt, gather sources for a note or rating.

    Here's the flow of how this function works:
        Prompt --> Search Query
        Search Query --> Results
        Results --> Choose N Results
        N Results --> N Summaries
        N Summaries --> Add to original prompt
        Return prompt
    """
    assert output_type in ["rating", "note"], "output_type must be Rating or Note"

    # Generate a search query
    prompt += prompts['search_query_prompt'].format(output_type=output_type)
    search_query = openai.chat.completions.create(
        model=endpoint,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20
    ).choices[0].message.content

    # Search the query
    search_results = search(search_query, num_results=10)

    # Loop through search results to summarize relevant sources
    urls, summaries = [], []
    try:
        for url in search_results:
            try:
                # Fetch the text from the URL
                response = requests.get(url, timeout=5)
                soup = BeautifulSoup(response.text, 'html.parser')
                text = soup.get_text()
                truncated_text = truncate_text(text, max_tokens=3000)
                text_preview = truncate_text(text, max_tokens=500)

                # Interact with ChatGPT to check if the source is useful and necessary
                relevance_response = openai.chat.completions.create(
                    model=endpoint,
                    messages=[{"role": "user", "content": prompt + format_sources(summaries, urls) + 
                        prompts['relevant_source_prompt'].format(url=url, text_preview=text_preview, output_type=output_type)
                    }]
                ).choices[0].message.content

                if "yes" in relevance_response.lower():
                    # Ask ChatGPT to write a brief summary
                    summary = openai.chat.completions.create(
                        model=endpoint,
                        messages=[{"role": "user", "content": prompt + format_sources(summaries, urls) + 
                            prompts['summarize_source_prompt'].format(url=url, text=truncated_text, output_type=output_type)
                        }]
                    ).choices[0].message.content

                    urls.append(url)
                    summaries.append(summary)

            except Exception as e:
                urls.append(url)
                summaries.append("The URL could not be fetched.")

            if len(summaries)==num_sources:
                break
    except Exception as e:
        print(e)
        pdb.set_trace()

    return format_sources(summaries, urls)