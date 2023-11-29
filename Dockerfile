# Use the official Python image as the base image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory
WORKDIR /app

# Copy the application files into the container
COPY . /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y libjpeg-dev zlib1g-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --trusted-host pypi.python.org firebase-admin

# Expose the port on which the application will run
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]
