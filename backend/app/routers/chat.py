from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.rag import CosmereRAGService

router = APIRouter(prefix="/chat", tags=["chat"])

# Initialize RAG service once
rag_service = CosmereRAGService()


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    sources: list


@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about the Cosmere"""
    try:
        result = rag_service.answer_question(request.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search(query: str, k: int = 5):
    """Direct similarity search (for debugging)"""
    try:
        results = rag_service.search_similar(query, k=k)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
