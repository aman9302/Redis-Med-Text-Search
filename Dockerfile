## Use the base image with Python and required dependencies
#
FROM python:3.9
#

## Set the working directory inside the container
#
WORKDIR /app
#

## Copy the requirements.txt and start.sh files into the container
#
COPY requirements.txt /app/requirements.txt
COPY start.sh /app/start.sh
#

## Install the required Python packages
#
RUN pip install --no-cache-dir -r requirements.txt
#

## Install Redis
#
RUN apt-get update && apt-get install -y redis-server
#

## Expose the Redis port (default: 6379)
#
EXPOSE 6379
#

## Set environment variables for Streamlit to connect to Redis
#
ENV REDIS_HOST=redis-server
ENV REDIS_PORT=6379
#

## Copy the mimic_case_data folder into the container
#
COPY mimic_case_data_redis /app/mimic_case_data_redis
#

## Set execute permission for the start.sh script
#
RUN chmod +x /app/start.sh
#

## Start the Redis server and Streamlit app using the start.sh script
#
CMD ["./start.sh"]
#



