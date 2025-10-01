# config.py

import os

# Firebase Configuration
SERVICE_ACCOUNT_FILE = './gcp/serviceAccountKey.json'

# Ollama Configuration
OLLAMA_BASE_URL = "http://ollama:11434"
OLLAMA_GENERATION_MODEL = "phi3:mini" # Using a powerful model for generation

# NLTK Configuration
# Ensures the punkt tokenizer is available.
try:
    import nltk
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Downloading NLTK 'punkt' model...")
    nltk.download('punkt')