FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libsentencepiece-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies - install sentencepiece and protobuf first for stability
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir protobuf sentencepiece scikit-learn && \
    pip install --no-cache-dir -r requirements.txt

# Remove build-essential to save space after installing dependencies
RUN apt-get purge -y --auto-remove build-essential && rm -rf /var/lib/apt/lists/*

# Copy only the backend source code
# We copy it into a 'backend' folder to support the relative imports in main.py
COPY backend /app/backend

# Create a mount point for the model
RUN mkdir /working

# Set environment variables
ENV MODEL_PATH=/working
ENV PYTHONUNBUFFERED=1

# Expose port 8000 for FastAPI
EXPOSE 8000

# Run uvicorn from /app so it can find the 'backend' package
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

