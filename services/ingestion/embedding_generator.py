"""
Embedding Generation Module

Generates text embeddings using sentence-transformers and handles
storage in vector databases or simple persistence.
"""

import logging
from typing import List, Dict, Any, Optional, Union
import numpy as np
import hashlib
import json
from pathlib import Path
import os

# Optional imports for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

# Optional imports for transformers (fallback)
try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    torch = None

# Optional imports for vector databases
try:
    import qdrant_client
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

# Optional imports for Pinecone
try:
    from pinecone import Pinecone, ServerlessSpec
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Handles text embedding generation and storage."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        vector_db: str = "faiss",  # Options: "qdrant", "faiss", "pinecone", "none"
        dimension: Optional[int] = None,
        cache_dir: str = "/tmp/embeddings_cache",
        **vector_db_kwargs
    ):
        """
        Initialize embedding generator.

        Args:
            model_name: Model name for sentence transformers
            vector_db: Vector database to use ("qdrant", "faiss", "pinecone", "none")
            dimension: Expected embedding dimension (auto-detected if None)
            cache_dir: Directory for caching embeddings
            **vector_db_kwargs: Additional arguments for vector database
        """
        self.model_name = model_name
        self.vector_db_type = vector_db.lower()
        self.dimension = dimension
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # Initialize embedding model
        self.model = None
        self.tokenizer = None
        self.device = 'cpu'

        # Detect GPU if available
        if torch and torch.cuda.is_available():
            self.device = 'cuda'
        elif hasattr(torch, 'mps') and torch.backends.mps.is_available():
            self.device = 'mps'

        # Load embedding model
        self._load_model()

        # Initialize vector database
        self.vector_db = self._init_vector_db(**vector_db_kwargs)

        # Cache for computed embeddings
        self.embedding_cache = {}

        logger.info(f"Initialized EmbeddingGenerator with {self.model_name} on {self.device}")

    def _load_model(self) -> None:
        """Load the embedding model."""
        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                self.model = SentenceTransformer(self.model_name)
                # Move to device
                if hasattr(self.model, 'to'):
                    self.model.to(self.device)

                # Set dimension if not specified
                if not self.dimension:
                    self.dimension = self.model.get_sentence_embedding_dimension()

            elif TRANSFORMERS_AVAILABLE:
                logger.warning("Using transformers fallback (less efficient)")
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()

                if not self.dimension:
                    # Try to infer dimension
                    self.dimension = self.model.embeddings.word_embeddings.embedding_dim

            else:
                logger.error("Neither sentence-transformers nor transformers available")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            self.model = None

    def _init_vector_db(self, **kwargs):
        """Initialize vector database."""
        if self.vector_db_type == "qdrant":
            return self._init_qdrant(**kwargs)
        elif self.vector_db_type == "faiss":
            return self._init_faiss(**kwargs)
        elif self.vector_db_type == "pinecone":
            return self._init_pinecone(**kwargs)
        else:
            logger.info("Using no vector database - embeddings will be returned only")
            return None

    def _init_qdrant(self, host: str = "localhost", port: int = 6333, collection_name: str = "political_docs", **kwargs):
        """Initialize Qdrant client."""
        if not QDRANT_AVAILABLE:
            logger.error("Qdrant not available")
            return None

        try:
            client = qdrant_client.QdrantClient(host=host, port=port)

            # Create collection if it doesn't exist
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=qdrant_client.VectorParams(
                        size=self.dimension,
                        distance=qdrant_client.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {collection_name}")

            return {
                'client': client,
                'collection_name': collection_name
            }

        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            return None

    def _init_faiss(self, index_file: str = "embeddings.faiss", metadata_file: str = "embeddings_metadata.json", **kwargs):
        """Initialize FAISS index."""
        if not FAISS_AVAILABLE:
            logger.error("FAISS not available")
            return None

        index_path = Path(self.cache_dir) / index_file
        metadata_path = Path(self.cache_dir) / metadata_file

        if index_path.exists():
            # Load existing index
            try:
                index = faiss.read_index(str(index_path))
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                index = faiss.IndexFlatL2(self.dimension or 384)
                metadata = {}
        else:
            index = faiss.IndexFlatL2(self.dimension or 384)
            metadata = {}

        return {
            'index': index,
            'metadata': metadata,
            'index_path': index_path,
            'metadata_path': metadata_path
        }

    def _init_pinecone(self, api_key: str = None, index_name: str = "political-docs", **kwargs):
        """Initialize Pinecone client."""
        if not PINECONE_AVAILABLE:
            logger.error("Pinecone not available")
            return None

        try:
            pc = Pinecone(api_key=api_key or os.getenv("PINECONE_API_KEY"))

            # Create index if it doesn't exist
            existing_indexes = [index.name for index in pc.list_indexes()]
            if index_name not in existing_indexes:
                pc.create_index(
                    name=index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(cloud="aws", region="us-east-1")
                )

            return {
                'client': pc,
                'index_name': index_name,
                'index': pc.Index(index_name)
            }

        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {e}")
            return None

    def generate_embeddings(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """
        Generate embeddings for text.

        Args:
            text: Text or list of texts to embed

        Returns:
            Embedding(s) as list(s) of floats
        """
        if not self.model:
            logger.error("No embedding model available")
            return []

        # Handle single text
        if isinstance(text, str):
            return self._generate_single_embedding(text)
        else:
            return self._generate_batch_embeddings(text)

    def _generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for single text."""
        # Check cache first
        text_hash = hashlib.md5(text.encode()).hexdigest()
        if text_hash in self.embedding_cache:
            return self.embedding_cache[text_hash]

        try:
            if SENTENCE_TRANSFORMERS_AVAILABLE and hasattr(self.model, 'encode'):
                embedding = self.model.encode(text, convert_to_tensor=False)
                embedding = embedding.tolist()

            elif TRANSFORMERS_AVAILABLE and self.tokenizer and self.model:
                inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self.model(**inputs)
                    embedding = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                    embedding = embedding.tolist() if hasattr(embedding, 'tolist') else embedding

            else:
                logger.error("No valid embedding method available")
                return []

            # Cache the result
            self.embedding_cache[text_hash] = embedding
            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return []

    def _generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        embeddings = []
        for text in texts:
            emb = self._generate_single_embedding(text)
            embeddings.append(emb)
        return embeddings

    def store_embeddings(self, package_id: str, embeddings: List[float], metadata: Dict[str, Any] = None) -> bool:
        """
        Store embeddings in vector database.

        Args:
            package_id: Document identifier
            embeddings: Embedding vector
            metadata: Additional metadata

        Returns:
            True if successful
        """
        if not self.vector_db:
            logger.warning("No vector database configured")
            return False

        try:
            if self.vector_db_type == "qdrant":
                return self._store_qdrant(package_id, embeddings, metadata)
            elif self.vector_db_type == "faiss":
                return self._store_faiss(package_id, embeddings, metadata)
            elif self.vector_db_type == "pinecone":
                return self._store_pinecone(package_id, embeddings, metadata)
            else:
                logger.error(f"Unknown vector database type: {self.vector_db_type}")
                return False

        except Exception as e:
            logger.error(f"Failed to store embeddings: {e}")
            return False

    def _store_qdrant(self, package_id: str, embeddings: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Store embeddings in Qdrant."""
        try:
            payload = {
                'package_id': package_id,
                'timestamp': str(np.datetime64('now')),
            }
            if metadata:
                payload.update(metadata)

            self.vector_db['client'].upsert(
                collection_name=self.vector_db['collection_name'],
                points=[
                    qdrant_client.PointStruct(
                        id=hash(package_id) % (2**63 - 1),  # Generate ID
                        vector=embeddings,
                        payload=payload
                    )
                ]
            )
            return True

        except Exception as e:
            logger.error(f"Qdrant storage failed: {e}")
            return False

    def _store_faiss(self, package_id: str, embeddings: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Store embeddings in FAISS."""
        try:
            # Add to index
            vectors = np.array([embeddings], dtype=np.float32)
            self.vector_db['index'].add(vectors)

            # Store metadata
            index = len(self.vector_db['metadata'])
            self.vector_db['metadata'][package_id] = {
                'index': index,
                'timestamp': str(np.datetime64('now')),
                'metadata': metadata or {}
            }

            # Save to disk
            faiss.write_index(self.vector_db['index'], str(self.vector_db['index_path']))
            with open(self.vector_db['metadata_path'], 'w') as f:
                json.dump(self.vector_db['metadata'], f)

            return True

        except Exception as e:
            logger.error(f"FAISS storage failed: {e}")
            return False

    def _store_pinecone(self, package_id: str, embeddings: List[float], metadata: Dict[str, Any] = None) -> bool:
        """Store embeddings in Pinecone."""
        try:
            payload = {
                'package_id': package_id,
                'timestamp': str(np.datetime64('now')),
            }
            if metadata:
                payload.update(metadata)

            self.vector_db['index'].upsert([
                {
                    'id': package_id,
                    'values': embeddings,
                    'metadata': payload
                }
            ])
            return True

        except Exception as e:
            logger.error(f"Pinecone storage failed: {e}")
            return False

    def search_similar(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar documents using embeddings.

        Args:
            query_text: Text to search for
            top_k: Number of results to return

        Returns:
            List of similar documents with scores
        """
        if not self.vector_db:
            logger.warning("No vector database configured for search")
            return []

        try:
            query_embedding = self.generate_embeddings(query_text)
            if not query_embedding:
                return []

            if self.vector_db_type == "qdrant":
                return self._search_qdrant(query_embedding, top_k)
            elif self.vector_db_type == "faiss":
                return self._search_faiss(query_embedding, top_k)
            elif self.vector_db_type == "pinecone":
                return self._search_pinecone(query_embedding, top_k)
            else:
                return []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _search_qdrant(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search in Qdrant."""
        try:
            results = self.vector_db['client'].search(
                collection_name=self.vector_db['collection_name'],
                query_vector=query_embedding,
                limit=top_k
            )

            return [
                {
                    'id': str(hit.id),
                    'score': hit.score,
                    'metadata': hit.payload
                }
                for hit in results
            ]

        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            return []

    def _search_faiss(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search in FAISS."""
        try:
            vectors = np.array([query_embedding], dtype=np.float32)
            scores, indices = self.vector_db['index'].search(vectors, top_k)

            results = []
            for score, idx in zip(scores[0], indices[0]):
                package_id = None
                metadata = {}

                # Find package_id by index
                for pid, data in self.vector_db['metadata'].items():
                    if data.get('index') == int(idx):
                        package_id = pid
                        metadata = data.get('metadata', {})
                        break

                if package_id:
                    results.append({
                        'id': package_id,
                        'score': float(score),
                        'metadata': metadata
                    })

            return results

        except Exception as e:
            logger.error(f"FAISS search failed: {e}")
            return []

    def _search_pinecone(self, query_embedding: List[float], top_k: int) -> List[Dict[str, Any]]:
        """Search in Pinecone."""
        try:
            results = self.vector_db['index'].query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )

            return [
                {
                    'id': match.id,
                    'score': match.score,
                    'metadata': match.metadata
                }
                for match in results.matches
            ]

        except Exception as e:
            logger.error(f"Pinecone search failed: {e}")
            return []


# Utility functions
def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.

    Args:
        embedding1: First embedding
        embedding2: Second embedding

    Returns:
        Similarity score (0-1)
    """
    try:
        import numpy as np
        v1 = np.array(embedding1)
        v2 = np.array(embedding2)

        dot_product = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    except Exception:
        return 0.0


def normalize_embedding(embedding: List[float]) -> List[float]:
    """
    Normalize embedding to unit length.

    Args:
        embedding: Input embedding

    Returns:
        Normalized embedding
    """
    try:
        import numpy as np
        vec = np.array(embedding)
        norm = np.linalg.norm(vec)
        if norm == 0:
            return embedding
        return (vec / norm).tolist()
    except Exception:
        return embedding


# Test function
def main():
    """Test embedding generation."""
    generator = EmbeddingGenerator()

    sample_text = "This is a test document about political policies and government procedures."

    embeddings = generator.generate_embeddings(sample_text)

    if embeddings:
        print(f"Generated embedding with {len(embeddings)} dimensions")
        print(f"Sample values: {embeddings[:5]}")
        print(f"Stored: {generator.store_embeddings('test-123', embeddings)}")

        # Search similar
        similar = generator.search_similar(sample_text)
        print(f"Similar documents: {len(similar)}")
    else:
        print("Embedding generation failed")


if __name__ == "__main__":
    main()
