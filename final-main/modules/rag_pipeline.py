import os
import logging
from langchain.chains import RetrievalQA
from modules.llm_factory import get_llm_provider
from modules.vector_db_factory import get_vector_database_provider

logger = logging.getLogger(__name__)


def build_rag_chain(
    vectorstore, llm_provider_name="gemini", vector_db_provider_name="pinecone"
):
    """Build a RAG chain using specified LLM and vector database providers."""
    try:
        # Get vector database provider for retriever
        vector_provider = get_vector_database_provider(vector_db_provider_name)
        retriever = vector_provider.get_retriever(vectorstore, search_kwargs={"k": 5})

        # Get LLM provider
        llm_provider = get_llm_provider(llm_provider_name)

        # Get LLM instance with appropriate parameters
        if llm_provider_name == "gemini":
            llm = llm_provider.get_llm(
                model="gemini-2.5-pro",
                temperature=0,
                convert_system_message_to_human=True,
            )
        elif llm_provider_name == "openai":
            llm = llm_provider.get_llm(model="gpt-4", temperature=0)
        elif llm_provider_name == "azure_openai":
            llm = llm_provider.get_llm(temperature=0)
        else:
            # Default LLM configuration
            llm = llm_provider.get_llm(temperature=0)

        # Build RAG chain
        rag_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
        )

        logger.info(
            f"[RAG] ✅ RAG pipeline built using {llm_provider_name} LLM and {vector_db_provider_name} vector DB"
        )
        return rag_chain

    except Exception as e:
        logger.error(f"[RAG] ❌ Failed to build RAG chain: {e}")
        raise
