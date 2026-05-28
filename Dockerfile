# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose the port Cloud Run will use
EXPOSE 8080

# Run with gunicorn (production WSGI server)
# Cloud Run injects PORT env var (default 8080)
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
