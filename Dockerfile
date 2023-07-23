# Use the base image with Python and required dependencies
FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app/requirements.txt

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables for Redis Labs credentials
ENV REDIS_HOST=redis-17518.c1.asia-northeast1-1.gce.cloud.redislabs.com
ENV REDIS_PORT=17518
ENV REDIS_PASSWORD=<password>

# Copy the application code into the container
COPY app.py /app/app.py

# Expose the port on which the app will run (default: 8501)
EXPOSE 8501

# Start the app
CMD ["streamlit", "run", "--server.port", "8501", "app.py"]
