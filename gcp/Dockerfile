# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data required by the application
# This is done here to be part of the build process
RUN python -c "import nltk; nltk.download('punkt', quiet=True)"

# Copy the application's source code and credentials into the container
COPY main.py .
COPY syllabus_parser.py .
COPY firebase_ops.py .
COPY quiz_generator.py .
COPY config.py .
COPY serviceAccountKey.json .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the uvicorn server with the FastAPI app from main.py
# Use --reload for development if needed, but remove it for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]