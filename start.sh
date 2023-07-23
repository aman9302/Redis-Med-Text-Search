#!/bin/bash

# Exit early on errors
set -eu

# Install Python 3 virtual env
VIRTUALENV=.data/venv

# Install the requirements
pip install -r requirements.txt

# Start the Redis server
redis-server --port 6379 &

# Wait for Redis server to start (add any necessary delay if needed)
sleep 5

# Start the Streamlit app
streamlit run --server.port 8501 app.py
