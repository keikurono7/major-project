# Knowell – AI-Powered Educational Platform

Knowell is a full-stack educational platform that uses AI to automate content generation (question papers, quizzes, assignments) and provide intelligent learning support for students and teachers.

## Features

- **Teacher Tools** – Generate question papers, quizzes, and assignments from uploaded syllabus content; monitor class analytics.
- **Student Tools** – Take quizzes, submit assignments, and track personal progress.
- **RAG Chatbot** – A retrieval-augmented generation chatbot (`support/`) that answers questions based on uploaded documents.
- **Firebase Integration** – Authentication, user management, and Firestore-backed data storage.
- **GCP Deployment** – Backend containerised with Docker and deployable to Google Cloud Platform.

## Repository Structure

```
major-project/
├── gcp/                  # Python FastAPI backend
│   ├── main.py           # Application entry point & API routes
│   ├── auth.py           # Authentication & authorisation
│   ├── firebase_ops.py   # Firestore database operations
│   ├── question_paper_generator.py
│   ├── quiz_generator.py
│   ├── assignment_generator.py
│   ├── syllabus_parser.py
│   ├── backend_api.py
│   ├── config.py
│   ├── Dockerfile
│   └── requirements.txt
├── knowell/              # React + Vite frontend
│   ├── src/
│   │   ├── components/   # Reusable UI components (student & teacher)
│   │   ├── contexts/     # AuthContext
│   │   ├── pages/        # Login, StudentHome, TeacherHome
│   │   └── services/     # API communication layer
│   └── package.json
├── support/              # RAG chatbot (Streamlit + LangChain + Ollama)
│   └── rag_bot.py
├── question_papers/      # Generated question paper output files
├── requirements.txt      # Python deps for the support chatbot
└── report.md             # Detailed implementation report
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS, React Router, Recharts |
| Backend | Python 3.10, FastAPI, Uvicorn |
| AI / LLM | Ollama (llama2), LangChain, ChromaDB |
| Database | Firebase Firestore |
| Auth | Firebase Authentication (JWT) |
| Infrastructure | Docker, Google Cloud Platform |

## Prerequisites

- **Node.js** ≥ 18 and npm
- **Python** ≥ 3.10
- **Ollama** running locally (`http://localhost:11434`) with the `llama2` model pulled
- A **Firebase** project with Firestore enabled and a service account key

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/keikurono7/major-project.git
cd major-project
```

### 2. Backend setup (`gcp/`)

```bash
cd gcp

# Copy and edit environment variables
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Place your Firebase service account key
cp /path/to/serviceAccountKey.json serviceAccountKey.json

# Start the API server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 3. Frontend setup (`knowell/`)

```bash
cd knowell

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 4. RAG Chatbot (`support/`)

```bash
# From the repo root
pip install -r requirements.txt

# Run the Streamlit chatbot
streamlit run support/rag_bot.py
```

## Docker (Backend)

```bash
cd gcp
docker build -t knowell-backend .
docker run -p 8000:8000 --env-file .env knowell-backend
```

## Environment Variables

Copy `gcp/.env.example` to `gcp/.env` and fill in the values:

| Variable | Description |
|---|---|
| `DEBUG` | Enable debug mode (`True` / `False`) |
| `OLLAMA_BASE_URL` | Ollama API base URL |
| `OLLAMA_MODEL` | Ollama model name (e.g. `llama2`) |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase service account JSON |
| `OUTPUT_DIR` | Directory for generated outputs |
| `QUESTION_PAPERS_DIR` | Sub-directory for question papers |
| `TEMP_DATA_DIR` | Temporary data directory |

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| POST | `/api/papers/generate` | Generate a question paper |
| GET | `/api/papers/list` | List all question papers |
| POST | `/api/quizzes/generate` | Generate a quiz |
| POST | `/api/quizzes/{id}/submit` | Submit quiz answers |
| POST | `/api/assignments/generate` | Generate an assignment |
| GET | `/api/students/{id}/progress` | Get student progress |
| GET | `/api/analytics/class/{id}` | Get class analytics |
| POST | `/api/content/upload` | Upload educational content |
| POST | `/api/syllabus/upload` | Upload a syllabus |
| GET | `/api/health` | Health check |

See `report.md` for the full implementation details.

## Contributing

1. Fork the repository and create a feature branch.
2. Make your changes with clear commit messages.
3. Open a pull request describing what you changed and why.

## License

This project is for academic purposes.
