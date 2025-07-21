"""
Documentation generation service.
"""

import asyncio
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from core.config import Settings
from core.exceptions import (
    RepositoryError,
    ProcessingError,
    VectorDatabaseError,
    LLMError,
)
from modules.chunker import load_and_split
from modules.clone_repo import clone_repo
from modules.vector_db_factory import get_vector_database_provider
from modules.llm_factory import get_llm_provider
from modules.rag_pipeline import build_rag_chain
from modules.generator import generate_design_doc
from utils.cleanup import cleanup_directory
from utils.validation import validate_repository_size, validate_file_types
from utils.doc_storage import DocumentationStorage

logger = logging.getLogger(__name__)


class DocumentationService:
    """Service for generating code documentation."""

    def __init__(self, settings: Settings):
        """
        Initialize documentation service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.doc_storage = DocumentationStorage(settings.docs_output_directory)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        Path(self.settings.temp_directory).mkdir(parents=True, exist_ok=True)
        Path(self.settings.repo_directory).mkdir(parents=True, exist_ok=True)
        Path(self.settings.docs_output_directory).mkdir(parents=True, exist_ok=True)

    async def generate_documentation(
        self,
        repo_url: str,
        repo_name: str,
        task_id: str,
        file_extensions: List[str],
        include_diagrams: bool = True,
        vector_db_provider: Optional[str] = None,
        llm_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate documentation for a repository.

        Args:
            repo_url: Repository URL
            repo_name: Repository name
            task_id: Task identifier
            file_extensions: File extensions to process
            include_diagrams: Whether to include diagrams

        Returns:
            Dict containing documentation and metadata

        Raises:
            RepositoryError: If repository operations fail
            ProcessingError: If processing fails
            VectorDatabaseError: If vector database operations fail
            LLMError: If LLM operations fail
        """
        start_time = time.time()
        repo_path = None

        # Override settings for this generation if providers are specified
        original_vector_db_provider = self.settings.vector_db_provider
        original_llm_provider = self.settings.llm_provider

        if vector_db_provider:
            self.settings.vector_db_provider = vector_db_provider
        if llm_provider:
            self.settings.llm_provider = llm_provider

        try:
            logger.info(
                f"Starting documentation generation for {repo_name} (task: {task_id})"
            )
            logger.info(
                f"Using Vector DB: {self.settings.vector_db_provider}, LLM: {self.settings.llm_provider}"
            )

            # Step 1: Clone repository
            repo_path = await self._clone_repository(repo_url, task_id)

            # Step 2: Validate repository
            await self._validate_repository(repo_path, file_extensions)

            # Step 3: Process and chunk files
            chunks = await self._process_repository(repo_path, file_extensions)

            # Step 4: Initialize vector database
            index_name = await self._initialize_vector_database(task_id)

            # Step 5: Ingest chunks to vector database
            vectorstore = await self._ingest_to_vector_database(chunks, index_name)

            # Step 6: Build RAG chain
            rag_chain = await self._build_rag_chain(vectorstore)

            # Step 7: Generate documentation
            documentation = await self._generate_documentation(
                rag_chain, repo_name, include_diagrams
            )

            # Step 8: Save documentation to file
            storage_info = self.doc_storage.save_documentation(
                repo_name=repo_name,
                documentation=documentation,
                metadata={
                    "task_id": task_id,
                    "processing_time": time.time() - start_time,
                    "chunks_processed": len(chunks),
                    "file_extensions": file_extensions,
                    "include_diagrams": include_diagrams,
                    "repo_url": None,  # Don't store sensitive repo URL
                },
            )

            processing_time = time.time() - start_time

            logger.info(
                f"Documentation generation completed for {repo_name} in {processing_time:.2f}s"
            )
            logger.info(f"Documentation saved to: {storage_info['doc_file']}")

            return {
                "documentation": documentation,
                "processing_time": processing_time,
                "chunks_processed": len(chunks),
                "repo_name": repo_name,
                "storage_info": storage_info,
            }

        except Exception as e:
            logger.error(f"Documentation generation failed for {repo_name}: {str(e)}")
            raise

        finally:
            # Restore original settings
            self.settings.vector_db_provider = original_vector_db_provider
            self.settings.llm_provider = original_llm_provider

            # Cleanup repository
            if repo_path:
                await self._cleanup_repository(repo_path)

    async def _clone_repository(self, repo_url: str, task_id: str) -> str:
        """
        Clone repository to temporary location.

        Args:
            repo_url: Repository URL
            task_id: Task identifier

        Returns:
            str: Path to cloned repository

        Raises:
            RepositoryError: If cloning fails
        """
        try:
            # Security: Use secure temporary directory with restricted permissions
            import tempfile
            import stat

            # Create secure temporary directory
            temp_dir = tempfile.mkdtemp(
                prefix=f"repo_{task_id}_", dir=self.settings.repo_directory
            )

            # Set restrictive permissions (owner only)
            os.chmod(temp_dir, stat.S_IRWXU)

            repo_path = os.path.join(temp_dir, "repo")

            # Run cloning in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, clone_repo, repo_url, repo_path)

            return repo_path

        except Exception as e:
            raise RepositoryError(f"Failed to clone repository: {str(e)}")

    async def _validate_repository(
        self, repo_path: str, file_extensions: List[str]
    ) -> None:
        """
        Validate repository size and content.

        Args:
            repo_path: Path to repository
            file_extensions: Allowed file extensions

        Raises:
            ProcessingError: If validation fails
        """
        try:
            # Validate repository size
            await validate_repository_size(repo_path, self.settings.max_repo_size_mb)

            # Validate file types
            await validate_file_types(
                repo_path, file_extensions, self.settings.max_file_size_mb
            )

        except Exception as e:
            raise ProcessingError(f"Repository validation failed: {str(e)}")

    async def _process_repository(
        self, repo_path: str, file_extensions: List[str]
    ) -> List[Any]:
        """
        Process repository files and create chunks.

        Args:
            repo_path: Path to repository
            file_extensions: File extensions to process

        Returns:
            List of document chunks

        Raises:
            ProcessingError: If processing fails
        """
        try:
            # Run processing in executor to avoid blocking
            loop = asyncio.get_event_loop()
            chunks = await loop.run_in_executor(
                None, self._load_and_split_with_extensions, repo_path, file_extensions
            )

            if not chunks:
                raise ProcessingError("No processable files found in repository")

            return chunks

        except Exception as e:
            raise ProcessingError(f"Failed to process repository files: {str(e)}")

    def _load_and_split_with_extensions(
        self, repo_path: str, file_extensions: List[str]
    ) -> List[Any]:
        """
        Load and split files with specified extensions.

        Args:
            repo_path: Path to repository
            file_extensions: File extensions to process

        Returns:
            List of document chunks
        """
        all_chunks = []

        # Process each extension separately as LangChain DirectoryLoader
        # doesn't support complex glob patterns with curly braces
        for extension in file_extensions:
            # Ensure extension starts with dot
            if not extension.startswith("."):
                extension = f".{extension}"

            glob_pattern = f"**/*{extension}"

            try:
                chunks = load_and_split(repo_path, glob_pattern)
                all_chunks.extend(chunks)
            except Exception as e:
                # Log warning but continue with other extensions
                logger.warning(
                    f"Failed to process files with extension {extension}: {str(e)}"
                )
                continue

        return all_chunks

    async def _initialize_vector_database(self, task_id: str) -> str:
        """
        Initialize vector database based on configured provider.

        Args:
            task_id: Task identifier

        Returns:
            str: Database identifier (index/collection name)

        Raises:
            VectorDatabaseError: If initialization fails
        """
        try:
            provider = get_vector_database_provider(self.settings.vector_db_provider)

            # Prepare initialization parameters based on provider
            if self.settings.vector_db_provider == "pinecone":
                # Shorten task_id to fit within Pinecone's 45-character limit
                short_task_id = task_id.replace("-", "")[:32]
                index_name = f"code-docs-{short_task_id}"

                # Run initialization in executor
                loop = asyncio.get_event_loop()
                db_id = await loop.run_in_executor(
                    None, lambda: provider.initialize(index_name=index_name)
                )

            elif self.settings.vector_db_provider == "faiss":
                db_id = provider.initialize(
                    index_path=self.settings.faiss_index_path,
                    index_name=self.settings.faiss_index_name,
                )

            elif self.settings.vector_db_provider == "qdrant":
                db_id = provider.initialize(
                    url=self.settings.qdrant_url,
                    collection_name=self.settings.qdrant_collection_name,
                )
            else:
                raise ValueError(
                    f"Unsupported vector database provider: {self.settings.vector_db_provider}"
                )

            logger.info(
                f"[VectorDB] ✅ Initialized {self.settings.vector_db_provider}: {db_id}"
            )
            return db_id

        except Exception as e:
            raise VectorDatabaseError(f"Failed to initialize vector database: {str(e)}")

    async def _ingest_to_vector_database(self, chunks: List[Any], db_id: str) -> Any:
        """
        Ingest chunks to vector database.

        Args:
            chunks: Document chunks
            db_id: Vector database identifier (index/collection name)

        Returns:
            Vector store instance

        Raises:
            VectorDatabaseError: If ingestion fails
        """
        try:
            provider = get_vector_database_provider(self.settings.vector_db_provider)
            llm_provider = get_llm_provider(self.settings.llm_provider)

            # Get embeddings
            embeddings = llm_provider.get_embeddings()

            # Run ingestion in executor
            loop = asyncio.get_event_loop()

            if self.settings.vector_db_provider == "pinecone":
                vectorstore = await loop.run_in_executor(
                    None,
                    lambda: provider.ingest_documents(
                        chunks, embeddings, index_name=db_id
                    ),
                )
            elif self.settings.vector_db_provider == "faiss":
                vectorstore = await loop.run_in_executor(
                    None,
                    lambda: provider.ingest_documents(
                        chunks, embeddings, index_path=db_id
                    ),
                )
            elif self.settings.vector_db_provider == "qdrant":
                vectorstore = await loop.run_in_executor(
                    None,
                    lambda: provider.ingest_documents(
                        chunks,
                        embeddings,
                        collection_name=db_id,
                        url=self.settings.qdrant_url,
                    ),
                )
            else:
                raise ValueError(
                    f"Unsupported vector database provider: {self.settings.vector_db_provider}"
                )

            return vectorstore

        except Exception as e:
            raise VectorDatabaseError(f"Failed to ingest to vector database: {str(e)}")

    async def _build_rag_chain(self, vectorstore: Any) -> Any:
        """
        Build RAG chain for document generation.

        Args:
            vectorstore: Vector store instance

        Returns:
            RAG chain instance

        Raises:
            LLMError: If RAG chain building fails
        """
        try:
            # Run RAG chain building in executor with provider settings
            loop = asyncio.get_event_loop()
            rag_chain = await loop.run_in_executor(
                None,
                lambda: build_rag_chain(
                    vectorstore,
                    llm_provider_name=self.settings.llm_provider,
                    vector_db_provider_name=self.settings.vector_db_provider,
                ),
            )

            return rag_chain

        except Exception as e:
            raise LLMError(f"Failed to build RAG chain: {str(e)}")

    async def _generate_documentation(
        self, rag_chain: Any, repo_name: str, include_diagrams: bool
    ) -> str:
        """
        Generate documentation using RAG chain.

        Args:
            rag_chain: RAG chain instance
            repo_name: Repository name
            include_diagrams: Whether to include diagrams

        Returns:
            str: Generated documentation

        Raises:
            LLMError: If documentation generation fails
        """
        try:
            # Run documentation generation in executor
            loop = asyncio.get_event_loop()
            documentation = await loop.run_in_executor(
                None, generate_design_doc, rag_chain, repo_name
            )

            return documentation

        except Exception as e:
            raise LLMError(f"Failed to generate documentation: {str(e)}")

    async def _cleanup_repository(self, repo_path: str) -> None:
        """
        Clean up cloned repository.

        Args:
            repo_path: Path to repository to clean up
        """
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cleanup_directory, repo_path)
            logger.info(f"Cleaned up repository at {repo_path}")

        except Exception as e:
            logger.warning(f"Failed to cleanup repository at {repo_path}: {str(e)}")

    def get_saved_documentation(self, repo_name: str) -> Optional[str]:
        """
        Get the latest saved documentation for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Documentation content or None if not found
        """
        return self.doc_storage.get_documentation_by_repo(repo_name)

    def list_all_documentation(self) -> List[Dict[str, Any]]:
        """
        Get list of all saved documentation with metadata.

        Returns:
            List of documentation metadata
        """
        return self.doc_storage.get_documentation_list()

    def cleanup_old_documentation(self, keep_versions: int = 3) -> int:
        """
        Clean up old documentation files.

        Args:
            keep_versions: Number of versions to keep per repository

        Returns:
            Number of files cleaned up
        """
        return self.doc_storage.cleanup_old_files(keep_versions)
