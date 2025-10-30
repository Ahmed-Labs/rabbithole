import numpy as np
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class RelevanceScorer:
    """Compute semantic relevance scores between papers using embeddings."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the relevance scorer.
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model = SentenceTransformer(model_name)
    
    def _get_paper_text(self, paper) -> str:
        """
        Extract text representation from a paper.
        
        Args:
            paper: ResearchPaper object
            
        Returns:
            Combined text from title and abstract
        """
        title = paper.title or ""
        abstract = paper.abstract or ""
        return f"{title}. {abstract}"
    
    def compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for a text string.
        
        Args:
            text: Input text
            
        Returns:
            Embedding vector
        """
        return self.model.encode(text, convert_to_numpy=True)
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Reshape for sklearn's cosine_similarity
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)
        return float(cosine_similarity(emb1, emb2)[0][0])
    
    def score_paper_relevance(self, root_paper, target_paper) -> float:
        """
        Compute relevance score between root paper and target paper.
        
        Args:
            root_paper: The root/reference paper (A in diagram)
            target_paper: The paper to score (B or C in diagram)
            
        Returns:
            Relevance score (0-1)
        """
        root_text = self._get_paper_text(root_paper)
        target_text = self._get_paper_text(target_paper)
        
        root_emb = self.compute_embedding(root_text)
        target_emb = self.compute_embedding(target_text)
        
        return self.compute_similarity(root_emb, target_emb)
    
    def score_references_recursive(
        self, 
        root_paper, 
        depth: int = 0,
        max_depth: int = 2,
        path_prob: float = 1.0
    ) -> List[Dict]:
        """
        Recursively score all papers in reference tree against root paper.
        
        Args:
            root_paper: The root paper to compare against
            depth: Current depth in tree
            max_depth: Maximum depth to traverse
            path_prob: Accumulated path probability
            
        Returns:
            List of dicts with paper info and scores
        """
        results = []
        
        if depth >= max_depth or not root_paper.references:
            return results
        
        for ref in root_paper.references:
            # Compute direct semantic similarity
            semantic_score = self.score_paper_relevance(root_paper, ref)
            
            # Path probability (could be based on citation count, recency, etc.)
            # For now, using a simple decay: 0.8 for direct refs, 0.6 for 2nd level
            edge_prob = 0.8 if depth == 0 else 0.6
            current_path_prob = path_prob * edge_prob
            
            # Combined relevance score
            combined_score = semantic_score * current_path_prob
            
            results.append({
                "paper_id": ref.id,
                "title": ref.title,
                "depth": depth + 1,
                "semantic_similarity": semantic_score,
                "path_probability": current_path_prob,
                "relevance_score": combined_score
            })
            
            # Recurse into references
            sub_results = self.score_references_recursive(
                ref, 
                depth=depth + 1, 
                max_depth=max_depth,
                path_prob=current_path_prob
            )
            results.extend(sub_results)
        
        return results


def compute_relevance_scores(root_paper, max_depth: int = 2) -> Tuple[List[Dict], RelevanceScorer]:
    """
    Convenience function to compute relevance scores for a paper tree.
    
    Args:
        root_paper: Root paper with references loaded
        max_depth: Maximum depth to traverse
        
    Returns:
        Tuple of (scored results list, scorer instance)
    """
    scorer = RelevanceScorer()
    
    # First, score immediate references (A → B)
    results = scorer.score_references_recursive(
        root_paper, 
        depth=0, 
        max_depth=max_depth
    )
    
    # Sort by relevance score
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return results, scorer