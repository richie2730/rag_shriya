"""
LLM provider factory for different language model services.
"""

import logging
import os
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def get_llm(self, **kwargs) -> Any:
        """Get LLM instance."""
        pass

    @abstractmethod
    def get_embeddings(self) -> Any:
        """Get embeddings instance."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")

    def get_llm(self, model: str = "gemini-2.5-pro", **kwargs) -> Any:
        """Get Gemini LLM instance."""
        if not self.is_configured():
            raise ValueError("Gemini API key not configured")

        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=self.api_key,
                **kwargs
            )
        except ImportError:
            raise ImportError("langchain-google-genai package not installed")

    def get_embeddings(self) -> Any:
        """Get Gemini embeddings instance."""
        if not self.is_configured():
            raise ValueError("Gemini API key not configured")

        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings

            return GoogleGenerativeAIEmbeddings(
                model="models/embedding-001",
                google_api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-google-genai package not installed")

    def is_configured(self) -> bool:
        """Check if Gemini is properly configured."""
        return bool(self.api_key)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")

    def get_llm(self, model: str = "gpt-4", **kwargs) -> Any:
        """Get OpenAI LLM instance."""
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")

        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model=model,
                openai_api_key=self.api_key,
                **kwargs
            )
        except ImportError:
            raise ImportError("langchain-openai package not installed")

    def get_embeddings(self) -> Any:
        """Get OpenAI embeddings instance."""
        if not self.is_configured():
            raise ValueError("OpenAI API key not configured")

        try:
            from langchain_openai import OpenAIEmbeddings

            return OpenAIEmbeddings(
                openai_api_key=self.api_key
            )
        except ImportError:
            raise ImportError("langchain-openai package not installed")

    def is_configured(self) -> bool:
        """Check if OpenAI is properly configured."""
        return bool(self.api_key)


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI LLM provider."""

    def __init__(self):
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        self.embedding_deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")

    def get_llm(self, **kwargs) -> Any:
        """Get Azure OpenAI LLM instance."""
        if not self.is_configured():
            raise ValueError("Azure OpenAI not properly configured")

        try:
            from langchain_openai import AzureChatOpenAI

            return AzureChatOpenAI(
                azure_endpoint=self.endpoint,
                openai_api_key=self.api_key,
                openai_api_version=self.api_version,
                deployment_name=self.deployment_name,
                **kwargs
            )
        except ImportError:
            raise ImportError("langchain-openai package not installed")

    def get_embeddings(self) -> Any:
        """Get Azure OpenAI embeddings instance."""
        if not self.is_configured():
            raise ValueError("Azure OpenAI not properly configured")

        if not self.embedding_deployment:
            raise ValueError("Azure OpenAI embedding deployment not configured")

        try:
            from langchain_openai import AzureOpenAIEmbeddings

            return AzureOpenAIEmbeddings(
                azure_endpoint=self.endpoint,
                openai_api_key=self.api_key,
                openai_api_version=self.api_version,
                deployment=self.embedding_deployment,
            )
        except ImportError:
            raise ImportError("langchain-openai package not installed")

    def is_configured(self) -> bool:
        """Check if Azure OpenAI is properly configured."""
        return bool(
            self.api_key and 
            self.endpoint and 
            self.deployment_name
        )


# Provider registry
_PROVIDERS: Dict[str, LLMProvider] = {
    "gemini": GeminiProvider(),
    "openai": OpenAIProvider(),
    "azure_openai": AzureOpenAIProvider(),
}


def get_llm_provider(provider_name: str) -> LLMProvider:
    """
    Get LLM provider by name.

    Args:
        provider_name: Name of the provider

    Returns:
        LLMProvider instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider_name not in _PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")

    provider = _PROVIDERS[provider_name]
    
    if not provider.is_configured():
        raise ValueError(f"LLM provider '{provider_name}' is not properly configured")

    return provider


def list_available_llm_providers() -> List[str]:
    """List all available LLM providers."""
    return list(_PROVIDERS.keys())


def get_configured_providers() -> List[str]:
    """Get list of properly configured providers."""
    configured = []
    for name, provider in _PROVIDERS.items():
        if provider.is_configured():
            configured.append(name)
    return configured