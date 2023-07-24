##### Aman Nair R
##### Redis-Med-Text-Search-App
####
###
##
#

## Import required packages
#
import os
import requests
import redis
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import streamlit as st

## Main Class For Redis Text Search
#
class RedisTextSearch:

    ## Redis Configuration Function
    #
    def __init__(self, api_url):
        # Hardcoded Redis credentials
        self.redis_host = 'redis-17518.c1.asia-northeast1-1.gce.cloud.redislabs.com'
        self.redis_port = 17518
        self.redis_password = 'qy3S0BOfokwVQTBAjEwto10e7k4u5mKl'
        
        self.redis_server = self.connect_to_redis()

        self.api_url = api_url
        self.texts = self.load_texts_from_url()
        self.bm25_model = None

    ## Connect to the Redis server using the provided credentials
    #
    def connect_to_redis(self):
        try:
            return redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                password=self.redis_password,
                decode_responses=True
            )
        except Exception as e:
            raise ValueError(f"Failed to connect to Redis. Error: {e}")

    ## Retrieve text files from the GitHub URLs provided by the requests API
    #
    def load_texts_from_url(self):
        texts = []
        file_urls = self.get_github_files()
        for url in file_urls:
            text = self.fetch_text_from_url(url)
            texts.append(text)
        return texts

    ## Retrieves the GitHub URLs using the requests API
    #
    def get_github_files(self):
        response = requests.get(self.api_url)
        if response.status_code == 200:
            data = response.json()
            urls = [item['download_url'] for item in data]
            return urls
        else:
            raise ValueError(f"Failed to fetch file URLs from GitHub API. Status code: {response.status_code}")    

    ## Retrieves the text from the text files
    #
    def fetch_text_from_url(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise ValueError(f"Failed to fetch content from URL. Status code: {response.status_code}")

    ## Stores the original text from the files in the Redis DB
    #
    def store_original_texts(self):
        for index, text in enumerate(self.texts):
            self.redis_server.set(index, text)

    ## Encodes the text and stores the embeddings in a separate column in the Redis DB
    #
    def store_embeddings(self):
        model = SentenceTransformer('all-MiniLM-L6-v2')  # Initialise the Sentence Transformer model
        for index, text in enumerate(self.texts):
            embedding = model.encode([text])[0]
            encoded_embedding_str = embedding.tolist()  # Convert ndarray to list
            self.redis_server.set(f"embedding:{index}", str(encoded_embedding_str))

    ## Builds the BM25 model with the tokenised texts
    #
    def build_bm25_model(self):
        tokenized_texts = [text.split() for text in self.texts]
        self.bm25_model = BM25Okapi(tokenized_texts)

    ## Searches the bm25 model using the query text
    #
    def search_bm25_redis(self, query_text, num_results=3):
        if self.bm25_model is None:
            self.build_bm25_model()

        tokenized_query = query_text.split()
        scores = self.bm25_model.get_scores(tokenized_query)

        result_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_results]
        similar_texts = []
        for index, result_index in enumerate(result_indices, start=1):
            text_key = self.redis_server.keys(f"embedding:{result_index}")[0]
            encoded_text = self.redis_server.get(text_key)
            original_text = self.redis_server.get(result_index)
            similar_texts.append(f"{index}. {original_text}")

        return similar_texts

## Redis Labs credentials
#
REDIS_HOST = 'redis-17518.c1.asia-northeast1-1.gce.cloud.redislabs.com'
REDIS_PORT = 17518
REDIS_PASSWORD = 'qy3S0BOfokwVQTBAjEwto10e7k4u5mKl'

## GitHub repository details
#
github_repo = 'aman9302/Redis-Med-Text-Search'
folder_path = 'mimic_case_data_redis'
api_url = f'https://api.github.com/repos/{github_repo}/contents/{folder_path}'

## Initialize RedisTextSearch with Redis Labs credentials and GitHub API URL
#
redis_app = RedisTextSearch(api_url)

## Streamlit app code
#
def main():
    st.title("Medical Text Search using Redis")

    # Search input
    query_text = st.text_input("Enter query:")

    # Search button
    if st.button("Search"):
        if query_text:
            # Perform search using RedisTextSearch
            results = redis_app.search_bm25_redis(query_text)
            # Display search results
            if results:
                st.header("Search Results:")
                for result in results:
                    st.write(result)
            else:
                st.write("No results found.")
        else:
            st.write("Please enter a query.")

if __name__ == '__main__':
    main()
