# Cosmere RAG System

A **Retrieval-Augmented Generation (RAG)** system that enables intelligent question-answering about Brandon Sanderson's Cosmere universe using the Coppermind Wiki as a knowledge base.

## 🎯 Project Overview

This project demonstrates modern AI/ML engineering practices by combining Large Language Models (LLMs), vector databases, and web technologies to create an interactive Q&A system. Users can ask questions about the Cosmere and receive accurate, cited answers generated from a comprehensive wiki knowledge base.

### Key Features

- **Intelligent Context Retrieval**: Uses semantic search with vector embeddings to find relevant information
- **Agentic RAG**: LangChain agent autonomously decides when to retrieve context
- **Source Attribution**: All answers include citations to original wiki pages
- **Local LLM Support**: Runs completely locally using Ollama (no API costs)
- **Full-Stack Implementation**: FastAPI backend + React frontend

## 🏗️ Architecture

```
User Question
     ↓
React Frontend (TypeScript)
     ↓
FastAPI REST API
     ↓
LangChain Agent
     ↓
Vector Database (ChromaDB) ← Semantic Search
     ↓
Ollama LLM (Llama 2)
     ↓
Generated Answer + Sources
```

### Technical Stack

**Backend**

- **FastAPI**: Modern async Python web framework
- **LangChain**: LLM orchestration and agent framework
- **ChromaDB**: Vector database for semantic search
- **Ollama**: Local LLM inference (Llama 3.1)
- **HuggingFace Transformers**: Text embeddings (`all-MiniLM-L6-v2`)

**Frontend**

- **React 18**: Modern UI framework
- **TypeScript**: Type-safe development
- **Vite**: Fast build tool and dev server
- **Axios**: HTTP client for API communication

**Data Pipeline**

- **Selenium**: Web automation for data collection
- **MediaWiki XML Parser**: Structured wiki content extraction
- **Custom Wiki Markup Cleaner**: Text preprocessing

## 📊 Technical Highlights

### RAG Pipeline

1. **Document Ingestion**
   - Downloaded entire Coppermind Wiki using Selenium
   - Parsed MediaWiki XML format
   - Cleaned wiki markup (templates, references, HTML)
   - Split into ~1000 character chunks with 200 character overlap
   - Generated vector embeddings using sentence transformers

2. **Retrieval & Generation**
   - User query → vector embedding
   - Semantic search retrieves top-K relevant chunks
   - LangChain agent uses retrieval tool to gather context
   - Ollama generates answer with source citations
   - Returns structured response with metadata

### Key Implementation Details

- **Chunk Strategy**: Recursive text splitting with overlap to preserve context
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions, fast inference)
- **Vector Store**: ChromaDB with persistent storage
- **LLM**: Llama 3.1 via Ollama
- **Agent Pattern**: Tool-based retrieval with content+artifact response format

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama
- Chrome/Chromium (for data collection only)

### Installation

**1. Clone the repository**

```bash
git clone https://github.com/bwu2018/rag-demo.git
cd rag-demo
```

**2. Backend Setup**

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install and start Ollama
# Visit https://ollama.com/download
ollama pull llama3.1
```

**3. Data Ingestion**

_Option A: Use provided data (if available)_

```bash
# Place coppermind.xml in backend/data/
python scripts/ingest_wiki.py
```

_Option B: Collect fresh data_

```bash
# Requires Chrome WebDriver
pip install selenium

# Collect wiki pages and export XML
python scripts/export_wiki.py

# Ingest the downloaded XML
python scripts/ingest_wiki.py
```

**4. Start Backend**

```bash
uvicorn app.main:app --reload
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

**5. Frontend Setup**

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
# Frontend available at http://localhost:5173
```

## 📁 Project Structure

```
rag-demo/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI application
│   │   ├── routers/
│   │   │   └── chat.py                # Q&A endpoint
│   │   └── services/
│   │       ├── rag.py                 # LangChain agent & RAG logic
│   │       └── wiki_ingestion.py      # Data processing pipeline
│   ├── scripts/
│   │   ├── export_wiki.py             # Wiki data collection
│   │   └── ingest_wiki.py             # XML to vector DB
│   ├── data/
│   │   └── chromadb/                  # Persistent vector store
│   └── requirements.txt
├── frontend/
│   ├── src/
|   |   ├── ChatInterface.tsx      # Main Q&A UI
│   │   ├── App.tsx
│   └── package.json
└── README.md
```

## 🔧 API Reference

### POST `/chat/ask`

Ask a question about the Cosmere.

**Request:**

```json
{
  "question": "Who is Kaladin?"
}
```

**Response:**

```json
{
  "answer": "Kaladin is a main character...",
  "sources": [
    {
      "title": "Kaladin",
      "content": "Kaladin Stormblessed is...",
      "url": "https://coppermind.net/wiki/Kaladin"
    }
  ]
}
```

### GET `/chat/search`

Direct similarity search (debugging).

**Query Parameters:**

- `query`: Search string
- `k`: Number of results (default: 5)
