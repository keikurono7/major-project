from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
from contextlib import asynccontextmanager

from app import (
    assignments, quizzes, question_papers, projects, 
    syllabus, chatbot, marks, schedules, analytics
)
from app.config import settings
from app.ollama import ollama_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up application...")
    health = await ollama_client.check_health()
    if not health:
        logger.warning("Ollama server is not responding. Please start Ollama.")
    else:
        models = await ollama_client.list_models()
        logger.info(f"Available Ollama models: {models}")
    yield
    # Shutdown
    logger.info("Shutting down application...")
    await ollama_client.close()

app = FastAPI(
    title="GCP AI Education API",
    description="AI-powered education platform with personalized learning schedules",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    logger.warning("Static directory not found")

# Include all routers
app.include_router(assignments.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(quizzes.router, prefix="/api/quizzes", tags=["Quizzes"])
app.include_router(question_papers.router, prefix="/api/question-papers", tags=["Question Papers"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(syllabus.router, prefix="/api/syllabus", tags=["Syllabus"])
app.include_router(chatbot.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(marks.router, prefix="/api/marks", tags=["Marks & BKT"])
app.include_router(schedules.router, prefix="/api/schedules", tags=["Personal Schedules"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics & Dashboards"])

@app.get("/")
async def root():
    return {
        "message": "GCP AI Education API",
        "version": "2.0.0",
        "features": [
            "Multi-source mark integration (Quiz, Assignment, PBL, IA, Semester Exams)",
            "Personalized learning schedules",
            "BKT-based knowledge tracking",
            "AI-powered content generation",
            "Real-time progress monitoring",
            "Class-wide analytics and heatmaps"
        ],
        "ai_engine": "Ollama",
        "model": settings.OLLAMA_MODEL,
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    ollama_status = await ollama_client.check_health()
    return {
        "status": "healthy",
        "ollama_connected": ollama_status,
        "model": settings.OLLAMA_MODEL
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=settings.DEBUG)