# Base Image
FROM python:3.11-slim

# Metadata
LABEL maintainer="anandhu723"
LABEL version="1.0.0"
LABEL created="2025-06-09"

# Set working directory
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy everything else
COPY . .

# Open port 8000
EXPOSE 8000

# Run the app
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:8000"]
