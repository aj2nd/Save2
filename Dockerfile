# Base Image
FROM python:3.11-slim
# Base Image
FROM python:3.11-slim

# Add build arguments for secrets
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB
ARG DATABASE_URL

# Set environment variables
ENV POSTGRES_USER=$POSTGRES_USER \
    POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    POSTGRES_DB=$POSTGRES_DB \
    DATABASE_URL=$DATABASE_URL

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
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:se
COPY . .

