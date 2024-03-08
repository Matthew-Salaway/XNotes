# An Automated LLM Fact-Checker 
This repository provides an automated system for running fact checks. It is built to fact-check Tweets, and to verify the accuracy of its fact-checks using historical data from Community Notes. The fact-checker is powered by OpenAI's GPT-3.5. 

To run this repository, for the first time:
1. Clone this Git repo.
2. Set up a Python virtual environment (venv). 
3. Install the packages in `requirements.txt`. 
4. Create a file called `.env` modeled after `.env.example`. Paste into that file the OpenAI API Key and a Twitter Bearer Token from Slack.

This repository consists of the following files:
1. `data.py` downloads Community Notes notes and ratings from Twitter, then merges and filters these files to clean the data. These files do not contain the text of Tweets themselves, as this is the proprietary data of Twitter and is not made freely available. Instead, we have purchased a subscription to Twitter's API plan, and `data.py` provides a function for fetching Tweet text using the API. 
2. `factchecker.py` writes notes and ratings for tweets. Its input is `master.csv`, and it saves a new version of `master.csv` for each new note or tweet. To help in the fact-checking process, it uses functions from `unfurl_links.py` and `websurfer.py`.
3. `unfurl_links.py` helps us handle text with links in it. For links to other Tweets, it uses the Twitter API to fetch the tweet text. For links to images and videos embedded in Tweets, it returns: `WARNING: This tweet contains an image or video that cannot be displayed.` For links to all other websites, it usesthe `requests` package to fetch text from the linked website. Sometimes, the website has a paywall or otherwise does not return relevant text; we do not have error handling for this case yet. 
4. `websurfer.py` searches the internet for sources to inform a note or rating. The steps are: generate a search query, search via Google, loop through the results, determine whether each result is relevant, and summarize the relevant results. The summarized search results are returned to the factchecker. 
5. `parallel_factchecker.py` is a parallelized version of `factchecker.py` which allows you to generate many ratings or fact checks at once.
6. `fine-tuning.py` provides code for fine-tuning GPT-3.5 on historical Community Notes data. Our initial results with this method were mixed, and therefore we do not plan to prioritize it in our upcoming experiments.  
6. `utils.py` contains functions that are commonly used in other files, such as `call_gpt()` and `truncate_text()`. 