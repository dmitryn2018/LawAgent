from abc import ABC, abstractmethod
from typing import Optional, List
import httpx
import hashlib
from loguru import logger

from app.core.config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self._dimension = 1536  # text-embedding-3-small default
    
    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [item.embedding for item in response.data]
    
    @property
    def dimension(self) -> int:
        return self._dimension


class OllamaEmbeddingProvider(EmbeddingProvider):
    """Ollama embedding provider."""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_embedding_model
        self._dimension = 768  # nomic-embed-text default
    
    async def embed(self, text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings
    
    @property
    def dimension(self) -> int:
        return self._dimension


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing."""
    
    def __init__(self):
        self._dimension = 1536
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate a deterministic mock embedding based on text hash."""
        # Use hash to generate consistent embeddings for same text
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        # Generate embedding from hash
        embedding = []
        for i in range(0, min(len(text_hash) * 48, self._dimension)):
            char_idx = i % len(text_hash)
            val = (ord(text_hash[char_idx]) - 48) / 100.0  # Normalize to small values
            embedding.append(val)
        
        # Pad if needed
        while len(embedding) < self._dimension:
            embedding.append(0.01)
        
        return embedding[:self._dimension]
    
    async def embed(self, text: str) -> List[float]:
        logger.debug(f"MockEmbedding generating embedding for text length: {len(text)}")
        return self._generate_mock_embedding(text)
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self._generate_mock_embedding(text) for text in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension


# Provider factory
_embedding_provider: Optional[EmbeddingProvider] = None


def get_embedding_provider() -> EmbeddingProvider:
    """Get the configured embedding provider instance."""
    global _embedding_provider
    
    if _embedding_provider is None:
        provider_type = settings.embedding_provider.lower()
        
        if provider_type == "openai":
            if not settings.openai_api_key:
                logger.warning("OpenAI API key not set, falling back to mock embedding provider")
                _embedding_provider = MockEmbeddingProvider()
            else:
                _embedding_provider = OpenAIEmbeddingProvider()
                logger.info("Using OpenAI embedding provider")
        elif provider_type == "ollama":
            _embedding_provider = OllamaEmbeddingProvider()
            logger.info(f"Using Ollama embedding provider at {settings.ollama_base_url}")
        else:
            _embedding_provider = MockEmbeddingProvider()
            logger.info("Using Mock embedding provider")
    
    return _embedding_provider

