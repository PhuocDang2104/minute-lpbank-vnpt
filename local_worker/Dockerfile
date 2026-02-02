# Dockerfile for HF Space
# Hugging Face Spaces sử dụng Docker runtime

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements_hf.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements_hf.txt

# Copy application code
COPY . .

# Expose port (HF Space uses 7860 by default)
EXPOSE 7860

# Set environment variables
ENV PORT=7860
ENV HF_HOME=/tmp/huggingface

# Run the application
CMD ["python", "app.py"]

