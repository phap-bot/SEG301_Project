from typing import List, Tuple, Dict

class HybridRanker:
    @staticmethod
    def search(bm25_results: List[Tuple[str, float, str]], vector_results: List[Tuple[str, float, str]], top_k: int = 50, k: int = 60) -> List[Tuple[str, float, str]]:
        """
        Combines BM25 and Vector results using Reciprocal Rank Fusion (RRF).
        RRF formula: score = 1 / (k + rank)
        
        Args:
            bm25_results: List of (doc_id, score, snippet) from BM25
            vector_results: List of (doc_id, score, snippet) from Vector Search
            top_k: Number of total results to return
            k: The RRF constant (default 60 is standard practice)
        Returns:
            Combines list of (doc_id, score, snippet) sorted by descending RRF score
        """
        rrf_scores: Dict[str, float] = {}
        snippets: Dict[str, str] = {}
        
        # Assign RRF scores for BM25 results
        for rank, res in enumerate(bm25_results):
            doc_id, score, snippet = res
            rrf_score = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score
            snippets[doc_id] = snippet  # Keep BM25 snippet as it usually has highlights
            
        # Assign RRF scores for Vector results
        for rank, res in enumerate(vector_results):
            doc_id, score, snippet = res
            rrf_score = 1.0 / (k + rank + 1)
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + rrf_score
            
            # If no snippet from BM25, use vector snippet (even if empty)
            if doc_id not in snippets:
                snippets[doc_id] = snippet
                
        # Sort by combined RRF score
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Format output
        final_results = []
        for doc_id, score in sorted_results[:top_k]:
            final_results.append((doc_id, score, snippets.get(doc_id, "")))
            
        return final_results
