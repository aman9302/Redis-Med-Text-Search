import os
import requests
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import redis
import ast
from flask import Flask, render_template, request

app = Flask(__name__)

class RedisTextSearch:
    def __init__(self, url_list):
        self.redis_server = redis.Redis()
        self.texts = self.load_texts_from_url(url_list)
        self.bm25_model = None

    def load_texts_from_url(self, url_list):
        texts = []
        for url in url_list:
            text = self.fetch_text_from_url(url)
            texts.append(text)
        return texts

    def fetch_text_from_url(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            raise ValueError(f"Failed to fetch content from URL. Status code: {response.status_code}")

    def store_original_texts(self):
        for index, text in enumerate(self.texts):
            self.redis_server.set(index, text)

    def store_embeddings(self):
        model = SentenceTransformer('all-MiniLM-L6-v2')
        for index, text in enumerate(self.texts):
            embedding = model.encode([text])[0]
            encoded_embedding_str = embedding.tolist()  # Convert ndarray to list
            self.redis_server.set(f"embedding:{index}", str(encoded_embedding_str))

    def build_bm25_model(self):
        tokenized_texts = [text.split() for text in self.texts]
        self.bm25_model = BM25Okapi(tokenized_texts)

    def search_bm25_redis(self, query_text, num_results=3):
        if self.bm25_model is None:
            self.build_bm25_model()

        tokenized_query = query_text.split()
        scores = self.bm25_model.get_scores(tokenized_query)

        result_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:num_results]
        similar_texts = []
        for index, result_index in enumerate(result_indices, start=1):
            text_key = self.redis_server.keys(f"embedding:{result_index}")[0]
            encoded_text = self.redis_server.get(text_key).decode()
            decoded_embedding = ast.literal_eval(encoded_text)
            original_text = self.redis_server.get(result_index).decode()
            similar_texts.append(f"{index}. {original_text}")

        return similar_texts

# Fetch file URLs from the GitHub repository folder using the GitHub API
def get_github_files(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        urls = [item['download_url'] for item in data]
        return urls
    else:
        raise ValueError(f"Failed to fetch file URLs from GitHub API. Status code: {response.status_code}")

# GitHub repository details
github_repo = 'aman9302/Redis-Med-Text-Search'
folder_path = 'mimic_case_data_redis'

# GitHub API endpoint to get the contents of a repository folder
api_url = f'https://api.github.com/repos/{github_repo}/contents/{folder_path}'

# Get file URLs
file_urls = get_github_files(api_url)

redis_app = RedisTextSearch(file_urls)
redis_app.store_original_texts()
redis_app.store_embeddings()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_text = request.form['query']
