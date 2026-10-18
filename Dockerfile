FROM python:3.11-slim

WORKDIR /app

# Ensure we have required system dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc netcat-traditional && rm -rf /var/lib/apt/lists/*

# Copy the requirements files
COPY requirements.txt ./
COPY backend/requirements.txt ./backend/

# Install the combined dependencies
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

# Also install pytest and httpx for running tests
RUN pip install --no-cache-dir pytest pytest-asyncio httpx

# Copy the rest of the application code
COPY . .

# Expose port for FastAPI
EXPOSE 8000

# Start command
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
