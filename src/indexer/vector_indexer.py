import os
import json
import pickle
import faiss
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIndexer:
    def __init__(self, model_name: str = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'):
        """
        Initializes the Vector Indexer with a semantic embedding model.
        Uses a lightweight multilingual model ideal for Vietnamese text.
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        # Vector dimensionality
        self.d = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.doc_mapping = {}

    def build_index(self, data_path: str, output_dir: str, chunk_size: int = 50000):
        """
        Reads JSONL data, embeds specific text fields, and builds a FAISS index in batches to save RAM.
        """
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Data file not found: {data_path}")

        os.makedirs(output_dir, exist_ok=True)
        
        # We will use Inner Product (Cosine Similarity if normalized)
        # or L2 distance. L2 is popular:
        self.index = faiss.IndexFlatL2(self.d)

        logger.info(f"Counting total lines in {data_path}...")
        with open(data_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
            
        logger.info(f"Total documents to process: {total_lines}")

        current_doc_idx = 0
        
        with open(data_path, 'r', encoding='utf-8') as f:
            texts_chunk = []
            ids_chunk = []
            
            pbar = tqdm(total=total_lines, desc="Indexing")
            
            for i, line in enumerate(f):
                if not line.strip():
                    pbar.update(1)
                    continue
                try:
                    product = json.loads(line)
                    doc_id = product.get("product_id") or str(i)
                    
                    # Create a rich text representation for the model
                    # Combining product name and category heavily helps semantic matching
                    name = product.get("product_name", "")
                    category = product.get("category", "")
                    
                    if not name:
                        pbar.update(1)
                        continue
                        
                    text_repr = f"{name} {category}".strip()
                    texts_chunk.append(text_repr)
                    ids_chunk.append(doc_id)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse line {i}")
                    pbar.update(1)
                    continue

                if len(texts_chunk) >= chunk_size:
                    self._process_chunk(texts_chunk, ids_chunk, current_doc_idx)
                    current_doc_idx += len(texts_chunk)
                    pbar.update(len(texts_chunk))
                    texts_chunk = []
                    ids_chunk = []

            # Process remaining documents
            if texts_chunk:
                self._process_chunk(texts_chunk, ids_chunk, current_doc_idx)
                current_doc_idx += len(texts_chunk)
                pbar.update(len(texts_chunk))
                
            pbar.close()

        logger.info(f"Total embedded documents: {current_doc_idx}")

        # Save to disk
        index_path = os.path.join(output_dir, "vector_index.faiss")
        mapping_path = os.path.join(output_dir, "vector_doc_mapping.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(mapping_path, 'wb') as f:
            pickle.dump(self.doc_mapping, f)
            
        logger.info(f"Successfully saved FAISS index to {index_path}")
        logger.info(f"Successfully saved Doc Mapping to {mapping_path}")

    def _process_chunk(self, texts_chunk, ids_chunk, start_idx):
        # Encode returns a numpy array representing vectors
        embeddings = self.model.encode(texts_chunk, batch_size=256, show_progress_bar=False, normalize_embeddings=True)
        # Add to FAISS index
        self.index.add(np.array(embeddings).astype('float32'))
        # Update mapping
        for i, doc_id in enumerate(ids_chunk):
            self.doc_mapping[start_idx + i] = str(doc_id)

if __name__ == "__main__":
    # Define paths
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    data_file = os.path.join(base_dir, "data_1tr_clean_tokenized.jsonl")
    index_out_dir = os.path.join(base_dir, "index")
    
    # Run the indexer
    indexer = VectorIndexer()
    indexer.build_index(data_path=data_file, output_dir=index_out_dir, chunk_size=50000)
