import os
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import redis
import ast
from flask import Flask, render_template, request

app = Flask(__name__)

class RedisTextSearch:
    def __init__(self, folder_path):
        self.redis_server = redis.Redis()
        self.folder_path = folder_path
        self.texts = self.load_texts_from_folder()
        self.bm25_model = None

    def load_texts_from_folder(self):
        texts = []
        for filename in os.listdir(self.folder_path):
            if filename.endswith('.txt'):
                file_path = os.path.join(self.folder_path, filename)
                with open(file_path, 'r') as file:
                    text = file.read()
                    texts.append(text)
        return texts

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

# Folder path for text files
folder_path = '/Users/304026/Downloads/Redis-Med-Text-Search-app/mimic_case_data_redis'
redis_app = RedisTextSearch(folder_path)
redis_app.store_original_texts()
redis_app.store_embeddings()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_text = request.form['query']
        results = redis_app.search_bm25_redis(query_text)
        return render_template('index.html', results=results, query=query_text)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
