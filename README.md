# Step 1
Run the download_datasets_into_data_folder() function in the data.py file
- This downloads the 5 data files from https://twitter.com/i/communitynotes/download-data and stores them in the data folder
- This is about 2.9 GB of data

To run this repository, you will need to create a file called '.env' with an OpenAI API Key and a Twitter Bearer Token. See .env.example for the correct formatting. See Slack for the Key and Token. 

This repository consists of the following files:
1. `data.py` downloads Community Notes notes and ratings from Twitter, then performs merges and filters to clean the data. The first time you use this repository, you should use `data.py` to build your own version of `master.csv`. Once you understand what's happening inside `data.py` and the contents of `master.csv`, you can delete your own version and replace it with the group version of `master.csv`. 
2. `factchecker.py` takes in `master.csv` as an input, and writes notes and ratings for each tweet. 
3. `parallel_factchecker.py` is a parallelized version of the file above. 
4. `unfurl_links.py` helps us handle text with links in it. 

scans text to see if it contains links. If it contains a link, it fetches the content of the webpage and returns the text

This repository consists of the following files. 