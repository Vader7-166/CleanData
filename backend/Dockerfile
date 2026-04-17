FROM python:3.12-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
# Note: we mount or copy /working separately or expect it via volume. 
# We'll expect /working to be mapped to /app/working or similar.
# The code currently looks at D:/Code/CleanData/working, we need to change it via env var.

ENV MODEL_PATH=/working

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
