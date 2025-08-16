FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/db /app/models

# Download and set up Ollama models in the build process
RUN ollama serve & \
    sleep 10 && \
    ollama pull nomic-embed-text && \
    ollama pull mistral:7b && \
    pkill ollama

# Expose port
EXPOSE 7860

# Create startup script
RUN echo '#!/bin/bash\n\
ollama serve &\n\
sleep 15\n\
if ! ollama list | grep -q "nomic-embed-text"; then\n\
    ollama pull nomic-embed-text\n\
fi\n\
if ! ollama list | grep -q "mistral:7b"; then\n\
    ollama pull mistral:7b\n\
fi\n\
streamlit run app.py --server.address 0.0.0.0 --server.port 7860 --server.headless true\n' > /app/start.sh

RUN chmod +x /app/start.sh

# Run the startup script
CMD ["/app/start.sh"]