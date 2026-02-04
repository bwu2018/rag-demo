from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat

app = FastAPI(
    title="Cosmere RAG API",
    description="Ask questions about Brandon Sanderson's Cosmere using RAG",
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)


@app.get("/")
def read_root():
    return {"message": "Cosmere RAG API", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
