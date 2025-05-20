# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
# Prevents Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Ensures Python output is sent straight to terminal without buffering
ENV PYTHONUNBUFFERED 1
# Set FLASK_ENV to production to ensure gunicorn is started by start_server.py
ENV FLASK_ENV=production
# Set FLASK_APP for the start_server.py and flask commands (if any directly used)
# The start_server.py script will derive the gunicorn app module from this.
ENV FLASK_APP=run.py
# Set the listening port, matching PROD_PORT in start_server.py
ENV PORT=8000

# Set the working directory in the container
WORKDIR /app

# Install system dependencies that might be needed by Python packages
# Example: psycopg2 needs libpq-dev for PostgreSQL
# Add others as required, e.g., build-essential, curl, etc.
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# The start_server.py script will handle checks and starting Gunicorn
CMD ["python", "start_server.py"] 