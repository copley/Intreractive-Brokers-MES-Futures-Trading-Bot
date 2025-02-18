# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Git (and any other OS-level dependencies if needed)
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file into the container at /app
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files into the container at /app
COPY . /app

# Optionally, expose a port if your bot requires it (e.g., for a dashboard)
# EXPOSE 5000

# Define the default command to run your bot
CMD ["python", "main.py"]
