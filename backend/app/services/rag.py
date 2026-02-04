from typing import Dict, List

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama


class CosmereRAGService:
    def __init__(self, persist_directory: str = "./app/data/chromadb"):
        # Initialize Ollama LLM
        self.llm = ChatOllama(model="llama3.1", temperature=0)

        # Initialize embeddings (same as ingestion)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Load existing vector store
        self.vectorstore = Chroma(
            collection_name="cosmere_wiki",
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

        # Create retrieval tool
        @tool(response_format="content_and_artifact")
        def retrieve_context(query: str):
            """Retrieve information from the Coppermind wiki to help answer questions about the Cosmere."""
            retrieved_docs = self.vectorstore.similarity_search(query, k=5)
            serialized = "\n\n".join(
                (
                    f"Source: {doc.metadata.get('title', 'Unknown')}\n"
                    f"URL: {doc.metadata.get('source', '')}\n"
                    f"Content: {doc.page_content}"
                )
                for doc in retrieved_docs
            )
            return serialized, retrieved_docs

        # System prompt for the agent
        system_prompt = (
            "You are a helpful assistant answering questions about Brandon Sanderson's Cosmere universe. "
            "You have access to a tool that retrieves context from the Coppermind Wiki. "
            "Use the tool to find relevant information before answering questions. "
            "Always cite your sources using the page titles provided. "
            "If you cannot find the answer in the retrieved context, say so clearly."
        )

        # Create agent with retrieval tool
        self.agent = create_agent(
            self.llm, tools=[retrieve_context], system_prompt=system_prompt
        )

    def answer_question(self, question: str) -> Dict:
        """
        Answer a question using RAG with agent

        Returns:
            dict with 'answer' and 'sources'
        """
        # Run the agent
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )

        # Extract the final answer from messages
        messages = result.get("messages", [])
        answer = ""
        sources = []

        # Get the last AI message
        for msg in reversed(messages):
            if hasattr(msg, "content") and msg.content:
                # Check if it's an AI message (not a tool message)
                if hasattr(msg, "type") and msg.type == "ai":
                    answer = msg.content
                    break
                elif not hasattr(msg, "type"):  # Fallback
                    answer = msg.content
                    break

        # Extract sources from tool messages
        for msg in messages:
            if hasattr(msg, "artifact") and msg.artifact:
                # Tool returned documents as artifacts
                for doc in msg.artifact:
                    sources.append(
                        {
                            "title": doc.metadata.get("title", "Unknown"),
                            "content": doc.page_content[:200] + "...",
                            "url": doc.metadata.get("source", ""),
                        }
                    )

        # Remove duplicate sources
        seen_titles = set()
        unique_sources = []
        for source in sources:
            if source["title"] not in seen_titles:
                seen_titles.add(source["title"])
                unique_sources.append(source)

        return {
            "answer": answer if answer else "I couldn't generate an answer.",
            "sources": unique_sources,
        }

    def search_similar(self, query: str, k: int = 5) -> List[Dict]:
        """Direct similarity search for debugging"""
        docs = self.vectorstore.similarity_search(query, k=k)
        return [
            {
                "title": doc.metadata.get("title"),
                "content": doc.page_content[:300],
                "url": doc.metadata.get("source"),
            }
            for doc in docs
        ]
