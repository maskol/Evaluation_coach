"""RAG (Retrieval-Augmented Generation) Service for Knowledge Base."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG service for semantic retrieval from knowledge base.

    Features:
    - Document chunking with overlap
    - Embedding generation (using ChromaDB's default embedding function)
    - Vector storage in ChromaDB
    - Semantic similarity search
    """

    def __init__(
        self,
        collection_name: str = "evaluation_coach_kb",
        persist_directory: Optional[str] = None,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        ollama_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ):
        """
        Initialize RAG service.

        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist ChromaDB data
            chunk_size: Size of each text chunk in characters
            chunk_overlap: Overlap between chunks for context continuity
            ollama_url: URL of the Ollama API server
            embedding_model: Name of the Ollama embedding model to use
        """
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_model = embedding_model

        # Set up persistence directory
        if persist_directory is None:
            base_dir = Path(__file__).parent.parent.parent
            persist_directory = str(base_dir / "data" / "chroma_db")

        os.makedirs(persist_directory, exist_ok=True)

        # Create Ollama embedding function
        self.embedding_function = embedding_functions.OllamaEmbeddingFunction(
            url=f"{ollama_url}/api/embeddings",
            model_name=embedding_model,
        )
        logger.info(f"Using Ollama embedding model: {embedding_model}")

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                chroma_client_auth_provider=None,
                chroma_client_auth_credentials=None,
                chroma_server_http_port=None,
            ),
        )

        # Get or create collection with Ollama embeddings
        try:
            self.collection = self.client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
            )
            logger.info(
                f"Loaded existing collection '{collection_name}' with {self.collection.count()} documents"
            )
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "description": "SAFe and Lean Agile knowledge base for AI Coach",
                    "embedding_model": embedding_model,
                },
            )
            logger.info(f"Created new collection '{collection_name}'")

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def index_knowledge_base(self, knowledge_base_path: Optional[str] = None) -> int:
        """
        Index all documents from the knowledge base directory.

        Args:
            knowledge_base_path: Path to knowledge base directory

        Returns:
            Number of chunks indexed
        """
        if knowledge_base_path is None:
            kb_path = Path(__file__).parent.parent / "data" / "knowledge_base"
        else:
            kb_path = Path(knowledge_base_path)

        if not kb_path.exists():
            logger.warning(f"Knowledge base path does not exist: {kb_path}")
            return 0

        # Check if already indexed
        if self.collection.count() > 0:
            logger.info(
                f"Knowledge base already indexed with {self.collection.count()} chunks"
            )
            return self.collection.count()

        chunks_indexed = 0
        documents = []
        metadatas = []
        ids = []

        # Process all text files in knowledge base
        for file_path in kb_path.glob("*.txt"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Skip empty files
                if not content.strip():
                    continue

                # Chunk the document
                chunks = self.text_splitter.split_text(content)

                # Create metadata and IDs for each chunk
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append(
                        {
                            "source": file_path.name,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                        }
                    )
                    ids.append(f"{file_path.stem}_chunk_{i}")

                logger.info(f"Processed {file_path.name}: {len(chunks)} chunks")
                chunks_indexed += len(chunks)

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}", exc_info=True)

        # Add all documents to ChromaDB in batch
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(
                f"Successfully indexed {chunks_indexed} chunks from {len(set(m['source'] for m in metadatas))} documents"
            )

        return chunks_indexed

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents based on semantic similarity.

        Args:
            query: User query or question
            top_k: Number of top results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of retrieved documents with content and metadata
        """
        if self.collection.count() == 0:
            logger.warning("Collection is empty, indexing knowledge base first...")
            self.index_knowledge_base()

        try:
            # Query ChromaDB with semantic search
            results = self.collection.query(
                query_texts=[query],
                n_results=top_k,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

            # Format results
            retrieved_docs = []
            if results and results["documents"] and len(results["documents"]) > 0:
                for i, doc in enumerate(results["documents"][0]):
                    retrieved_docs.append(
                        {
                            "content": doc,
                            "metadata": (
                                results["metadatas"][0][i]
                                if results["metadatas"]
                                else {}
                            ),
                            "similarity_score": (
                                1 - results["distances"][0][i]
                                if results["distances"]
                                else 0
                            ),
                        }
                    )

            logger.info(
                f"Retrieved {len(retrieved_docs)} documents for query: '{query[:50]}...'"
            )
            return retrieved_docs

        except Exception as e:
            logger.error(f"Error during retrieval: {e}", exc_info=True)
            return []

    def reset_collection(self):
        """Reset the collection (useful for re-indexing)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "description": "SAFe and Lean Agile knowledge base for AI Coach",
                    "embedding_model": self.embedding_model,
                },
            )
            logger.info(f"Reset collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}", exc_info=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the indexed knowledge base."""
        count = self.collection.count()

        # Get unique sources
        if count > 0:
            sample = self.collection.get(limit=count, include=["metadatas"])
            sources = (
                set(m["source"] for m in sample["metadatas"])
                if sample["metadatas"]
                else set()
            )
        else:
            sources = set()

        return {
            "total_chunks": count,
            "total_documents": len(sources),
            "sources": sorted(sources),
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }


# Singleton instance
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Get or create the singleton RAG service instance."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
        # Only index if collection is empty
        if _rag_service.collection.count() == 0:
            _rag_service.index_knowledge_base()
    return _rag_service


if __name__ == "__main__":
    # Test the RAG service
    logging.basicConfig(level=logging.INFO)

    rag = RAGService()

    # Index knowledge base
    print("\n=== Indexing Knowledge Base ===")
    num_chunks = rag.index_knowledge_base()
    print(f"Indexed {num_chunks} chunks")

    # Get stats
    print("\n=== Collection Statistics ===")
    stats = rag.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Test retrieval
    print("\n=== Testing Retrieval ===")
    test_queries = [
        "How do I write a good Epic?",
        "What is the difference between an Epic and a Feature?",
        "How to reduce lead time?",
        "What is a Lean Business Case?",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        results = rag.retrieve(query, top_k=3)
        for i, doc in enumerate(results, 1):
            print(
                f"  {i}. [{doc['metadata']['source']}] (score: {doc['similarity_score']:.3f})"
            )
            print(f"     {doc['content'][:150]}...")
