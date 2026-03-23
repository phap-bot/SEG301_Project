import os
import faiss
import pickle
import numpy as np
import logging
from typing import List, Tuple
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class VectorRanker:
    def __init__(self, index_dir: str, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Loads the FAISS index and the embedding model for runtime search.
        """
        self.model = SentenceTransformer(model_name)
        
        index_path = os.path.join(index_dir, "vector_index.faiss")
        mapping_path = os.path.join(index_dir, "vector_doc_mapping.pkl")
        
        if not os.path.exists(index_path) or not os.path.exists(mapping_path):
            raise FileNotFoundError(f"Missing vector index files in {index_dir}")
            
        logger.info(f"Loading FAISS index from {index_path}")
        self.index = faiss.read_index(index_path)
        
        logger.info(f"Loading Doc Mapping from {mapping_path}")
        with open(mapping_path, 'rb') as f:
            self.doc_mapping = pickle.load(f)

    def search(self, query: str, top_k: int = 50) -> List[Tuple[str, float, str]]:
        """
        Embeds the query and searches the FAISS index.
        Returns: list of (doc_id, score, text_snippet)
        Note: FAISS L2 distance implies lower is better, but we return a transformed score so higher is better for consistency.
        """
        # Encode query
        query_vector = self.model.encode([query], normalize_embeddings=True)
        query_vector = np.array(query_vector).astype('float32')
        
        # Search FAISS
        # D is distances (L2), I is indices
        D, I = self.index.search(query_vector, k=top_k)
        
        results = []
        for dist, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            doc_id = self.doc_mapping.get(idx)
            if doc_id is not None:
                # Convert L2 distance to a similarity score (higher is better)
                # Since L2 distances for normalized vectors are between 0 and 4,
                # we can use a simple inversion or 1 / (1 + dist)
                score = 1.0 / (1.0 + dist)
                
                # We return an empty text_snippet to match BM25 signature
                results.append((doc_id, score, ""))
                
        return results
