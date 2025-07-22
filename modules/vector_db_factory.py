"""
Vector database provider factory for different vector database services.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class VectorDatabaseProvider(ABC):
    """Abstract base class for vector database providers."""

    @abstractmethod
    def initialize(self, **kwargs) -> str:
        """Initialize the vector database."""
        pass

    @abstractmethod
    def ingest_documents(self, documents: List[Any], embeddings: Any, **kwargs) -> Any:
        """Ingest documents into the vector database."""
        pass

    @abstractmethod
    def get_retriever(self, vectorstore: Any, **kwargs) -> Any:
        """Get retriever from vectorstore."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass


class PineconeProvider(VectorDatabaseProvider):
    """Pinecone vector database provider."""

    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.environment = os.getenv("PINECONE_ENV", "us-east-1-aws")

    def initialize(self, index_name: str = "code-docs", **kwargs) -> str:
        """Initialize Pinecone index."""
        if not self.is_configured():
            raise ValueError("Pinecone API key not configured")

        try:
            import pinecone
            from pinecone import Pinecone

            # Initialize Pinecone
            pc = Pinecone(api_key=self.api_key)

            # Check if index exists, create if not
            existing_indexes = [index.name for index in pc.list_indexes()]
            
            if index_name not in existing_indexes:
                pc.create_index(
                    name=index_name,
                    dimension=768,  # Default dimension for most embeddings
                    metric="cosine",
                    spec=pinecone.ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                logger.info(f"Created new Pinecone index: {index_name}")
            else:
                logger.info(f"Using existing Pinecone index: {index_name}")

            return index_name

        except ImportError:
            raise ImportError("pinecone package not installed")

    def ingest_documents(self, documents: List[Any], embeddings: Any, index_name: str, **kwargs) -> Any:
        """Ingest documents into Pinecone."""
        try:
            from langchain_pinecone import PineconeVectorStore

            vectorstore = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=embeddings,
                index_name=index_name
            )

            logger.info(f"Ingested {len(documents)} documents into Pinecone index: {index_name}")
            return vectorstore

        except ImportError:
            raise ImportError("langchain-pinecone package not installed")

    def get_retriever(self, vectorstore: Any, **kwargs) -> Any:
        """Get retriever from Pinecone vectorstore."""
        return vectorstore.as_retriever(**kwargs)

    def is_configured(self) -> bool:
        """Check if Pinecone is properly configured."""
        return bool(self.api_key)


class FaissProvider(VectorDatabaseProvider):
    """FAISS vector database provider."""

    def initialize(self, index_path: str = "./faiss_indexes", index_name: str = "code-docs", **kwargs) -> str:
        """Initialize FAISS index path."""
        import os
        os.makedirs(index_path, exist_ok=True)
        full_path = os.path.join(index_path, index_name)
        logger.info(f"FAISS index path: {full_path}")
        return full_path

    def ingest_documents(self, documents: List[Any], embeddings: Any, index_path: str, **kwargs) -> Any:
        """Ingest documents into FAISS."""
        try:
            from langchain_faiss import FAISS

            vectorstore = FAISS.from_documents(
                documents=documents,
                embedding=embeddings
            )

            # Save the index
            vectorstore.save_local(index_path)
            logger.info(f"Ingested {len(documents)} documents into FAISS index: {index_path}")
            return vectorstore

        except ImportError:
            raise ImportError("langchain-faiss package not installed")

    def get_retriever(self, vectorstore: Any, **kwargs) -> Any:
        """Get retriever from FAISS vectorstore."""
        return vectorstore.as_retriever(**kwargs)

    def is_configured(self) -> bool:
        """Check if FAISS is configured (always true as it's local)."""
        return True


class QdrantProvider(VectorDatabaseProvider):
    """Qdrant vector database provider."""

    def __init__(self):
        self.url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.api_key = os.getenv("QDRANT_API_KEY")

    def initialize(self, collection_name: str = "code-docs", url: Optional[str] = None, **kwargs) -> str:
        """Initialize Qdrant collection."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            client = QdrantClient(
                url=url or self.url,
                api_key=self.api_key
            )

            # Check if collection exists, create if not
            collections = client.get_collections().collections
            collection_names = [col.name for col in collections]

            if collection_name not in collection_names:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
                logger.info(f"Created new Qdrant collection: {collection_name}")
            else:
                logger.info(f"Using existing Qdrant collection: {collection_name}")

            return collection_name

        except ImportError:
            raise ImportError("qdrant-client package not installed")

    def ingest_documents(self, documents: List[Any], embeddings: Any, collection_name: str, url: Optional[str] = None, **kwargs) -> Any:
        """Ingest documents into Qdrant."""
        try:
            from langchain_qdrant import QdrantVectorStore

            vectorstore = QdrantVectorStore.from_documents(
                documents=documents,
                embedding=embeddings,
                url=url or self.url,
                api_key=self.api_key,
                collection_name=collection_name
            )

            logger.info(f"Ingested {len(documents)} documents into Qdrant collection: {collection_name}")
            return vectorstore

        except ImportError:
            raise ImportError("langchain-qdrant package not installed")

    def get_retriever(self, vectorstore: Any, **kwargs) -> Any:
        """Get retriever from Qdrant vectorstore."""
        return vectorstore.as_retriever(**kwargs)

    def is_configured(self) -> bool:
        """Check if Qdrant is configured."""
        return bool(self.url)  # URL is required, API key is optional


# Provider registry
_PROVIDERS: Dict[str, VectorDatabaseProvider] = {
    "pinecone": PineconeProvider(),
    "faiss": FaissProvider(),
    "qdrant": QdrantProvider(),
}


def get_vector_database_provider(provider_name: str) -> VectorDatabaseProvider:
    """
    Get vector database provider by name.

    Args:
        provider_name: Name of the provider

    Returns:
        VectorDatabaseProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider_name not in _PROVIDERS:
        raise ValueError(f"Unsupported vector database provider: {provider_name}")

    provider = _PROVIDERS[provider_name]
    
    if not provider.is_configured():
        raise ValueError(f"Vector database provider '{provider_name}' is not properly configured")

    return provider


def list_available_providers() -> List[str]:
    """List all available vector database providers."""
    return list(_PROVIDERS.keys())


def get_configured_providers() -> List[str]:
    """Get list of properly configured providers."""
    configured = []
    for name, provider in _PROVIDERS.items():
        if provider.is_configured():
            configured.append(name)
    return configured