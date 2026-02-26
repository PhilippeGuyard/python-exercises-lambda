FROM python:3.12-slim

# Install zip utility
RUN apt-get update && apt-get install -y zip

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --target ./package -r requirements.txt

# Copy application source
COPY lambda_function.py topics_list.py ./

# Create deployment zip
RUN cd package && zip -r9 /lambda_function.zip . && cd .. && zip -g /lambda_function.zip lambda_function.py topics_list.py

