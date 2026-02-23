# Use stable Python version (NOT 3.14)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Expose port (Render uses 10000)
EXPOSE 10000

# Start Flask app using gunicorn (production server)
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000"]