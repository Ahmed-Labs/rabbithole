import numpy as np
import hashlib
import pickle
import torch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from transformers import AutoTokenizer
from adapters import AutoAdapterModel
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingCache:
    """Simple file-based cache for paper embeddings."""
    
    def __init__(self, cache_dir: str = ".embedding_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def _get_cache_key(self, text: str, model_name: str) -> str:
        """Generate cache key from text and model name."""
        combined = f"{model_name}:{text}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get(self, text: str, model_name: str) -> Optional[np.ndarray]:
        """Retrieve embedding from cache."""
        key = self._get_cache_key(text, model_name)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def set(self, text: str, model_name: str, embedding: np.ndarray):
        """Store embedding in cache."""
        key = self._get_cache_key(text, model_name)
        cache_file = self.cache_dir / f"{key}.pkl"
        
        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)


class RelevanceScorer:
    """
    Compute semantic relevance scores between papers using SPECTER2 embeddings.
    
    SPECTER2 uses a base model + task-specific adapters. For paper similarity/retrieval,
    we use the 'proximity' adapter which is trained for finding similar papers.
    
    Inspired by ConnectedPapers methodology:
    - Co-citation analysis (papers cited together)
    - Bibliographic coupling (papers sharing references)
    - Publication year proximity
    """
    
    def __init__(
        self, 
        base_model: str = "allenai/specter2_base",
        adapter_name: str = "allenai/specter2",
        use_cache: bool = True,
        cache_dir: str = ".embedding_cache"
    ):
        """
        Initialize the relevance scorer with SPECTER2.
        
        Args:
            base_model: SPECTER2 base model name
            adapter_name: Adapter to use (proximity is best for paper similarity)
            use_cache: Whether to cache embeddings
            cache_dir: Directory for embedding cache
        """
        print(f"Loading SPECTER2 base model: {base_model}")
        print("(This may take a few minutes on first run)")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.model = AutoAdapterModel.from_pretrained(base_model)
        
        # Load and activate the proximity adapter for paper similarity
        print(f"Loading adapter: {adapter_name}")
        self.model.load_adapter(adapter_name, source="hf", set_active=True)
        
        self.model_name = f"{base_model}+{adapter_name}"
        self.use_cache = use_cache
        self.cache = EmbeddingCache(cache_dir) if use_cache else None
        
        # Move to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
        print(f"✓ Model loaded successfully on {self.device}")
    
    def _get_paper_text(self, paper) -> str:
        """
        Extract text representation from a paper.
        SPECTER2 is trained on title+abstract with SEP token between them.
        """
        title = paper.title or ""
        abstract = paper.abstract or ""
        # SPECTER2 uses SEP token between title and abstract
        return f"{title}{self.tokenizer.sep_token}{abstract}".strip()
    
    def compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for a text string with caching.
        """
        if self.use_cache and self.cache:
            cached = self.cache.get(text, self.model_name)
            if cached is not None:
                return cached
        
        # Tokenize
        inputs = self.tokenizer(
            [text],
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=512,
            return_token_type_ids=False
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get embeddings
        with torch.no_grad():
            output = self.model(**inputs)
            # Take the [CLS] token embedding (first token)
            embedding = output.last_hidden_state[:, 0, :].cpu().numpy()[0]
        
        if self.use_cache and self.cache:
            self.cache.set(text, self.model_name, embedding)
        
        return embedding
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        emb1 = embedding1.reshape(1, -1)
        emb2 = embedding2.reshape(1, -1)
        return float(cosine_similarity(emb1, emb2)[0][0])
    
    def _compute_year_similarity(self, year1: Optional[int], year2: Optional[int]) -> float:
        """
        Compute year proximity score (ConnectedPapers prioritizes similar generations).
        Returns 1.0 for same year, decaying with distance.
        """
        if year1 is None or year2 is None:
            return 0.5  # neutral if year unknown
        
        year_diff = abs(year1 - year2)
        
        # Decay function: 1.0 at 0 years, 0.5 at 5 years, ~0.2 at 10 years
        return np.exp(-year_diff / 5.0)
    
    def _compute_bibliographic_coupling(self, paper1, paper2) -> float:
        """
        Compute bibliographic coupling: how many references they share.
        This is what ConnectedPapers uses alongside co-citation.
        """
        if not paper1.references or not paper2.references:
            return 0.0
        
        refs1 = {ref.id for ref in paper1.references}
        refs2 = {ref.id for ref in paper2.references}
        
        shared = len(refs1 & refs2)
        total = len(refs1 | refs2)
        
        return shared / total if total > 0 else 0.0
    
    def _get_citation_score(self, paper) -> float:
        """
        Normalize citation count to 0-1 range.
        More citations = potentially more important paper.
        """
        if not hasattr(paper, 'citation_count') or paper.citation_count is None:
            return 0.5
        
        # Log scale normalization (most papers have 0-1000 citations)
        # Score: 0.5 at 100 citations, ~0.7 at 1000 citations
        return min(0.5 + np.log10(paper.citation_count + 1) / 6, 1.0)
    
    def _get_paper_year(self, paper) -> Optional[int]:
        """Extract publication year from paper metadata."""
        if hasattr(paper, 'year') and paper.year:
            return int(paper.year)
        return None
    
    def score_paper_relevance(
        self, 
        root_paper, 
        target_paper,
        include_metadata: bool = True
    ) -> Dict[str, float]:
        """
        Compute comprehensive relevance score between papers.
        
        Returns dict with multiple scoring components:
        - semantic_similarity: SPECTER2 embedding similarity
        - bibliographic_coupling: shared reference ratio
        - year_similarity: publication year proximity
        - citation_score: normalized citation count
        - combined_score: weighted combination
        """
        # Semantic similarity (primary signal)
        root_text = self._get_paper_text(root_paper)
        target_text = self._get_paper_text(target_paper)
        
        root_emb = self.compute_embedding(root_text)
        target_emb = self.compute_embedding(target_text)
        
        semantic_sim = self.compute_similarity(root_emb, target_emb)
        
        if not include_metadata:
            return {
                'semantic_similarity': semantic_sim,
                'combined_score': semantic_sim
            }
        
        # Additional signals (ConnectedPapers-inspired)
        bib_coupling = self._compute_bibliographic_coupling(root_paper, target_paper)
        
        root_year = self._get_paper_year(root_paper)
        target_year = self._get_paper_year(target_paper)
        year_sim = self._compute_year_similarity(root_year, target_year)
        
        citation_score = self._get_citation_score(target_paper)
        
        # Weighted combination (tunable)
        # Semantic similarity is most important, others are supplementary
        combined = (
            0.70 * semantic_sim +
            0.15 * bib_coupling +
            0.10 * year_sim +
            0.05 * citation_score
        )
        
        return {
            'semantic_similarity': semantic_sim,
            'bibliographic_coupling': bib_coupling,
            'year_similarity': year_sim,
            'citation_score': citation_score,
            'combined_score': combined
        }
    
    def score_all_papers(
        self,
        root_paper,
        max_depth: int = 2,
        path_prob: float = 1.0
    ) -> List[Dict]:
        """
        Score all papers in the graph (both references and citations).
        
        Args:
            root_paper: Root paper with references and citations populated
            max_depth: Maximum depth for both references and citations
            path_prob: Starting path probability
            
        Returns:
            List of scored papers with metadata
        """
        results = []
        seen_papers = {root_paper.id}  # Track to avoid duplicates
        
        # Score references recursively (papers this paper cites)
        def score_references(paper, depth, prob, edge_type="reference"):
            if depth >= max_depth or not paper.references:
                return
            
            for ref in paper.references:
                if ref.id in seen_papers:
                    continue
                seen_papers.add(ref.id)
                
                scores = self.score_paper_relevance(root_paper, ref)
                
                # Path probability decay
                edge_prob = 0.8 if depth == 0 else 0.6
                current_prob = prob * edge_prob
                
                final_relevance = scores['combined_score'] * current_prob
                
                results.append({
                    "paper_id": ref.id,
                    "title": ref.title,
                    "depth": depth + 1,
                    "edge_type": "reference",  # This paper cites ref
                    "semantic_similarity": scores['semantic_similarity'],
                    "bibliographic_coupling": scores['bibliographic_coupling'],
                    "year_similarity": scores['year_similarity'],
                    "citation_score": scores['citation_score'],
                    "combined_score": scores['combined_score'],
                    "path_probability": current_prob,
                    "relevance_score": final_relevance
                })
                
                score_references(ref, depth + 1, current_prob, edge_type)
        
        # Score citations recursively (papers that cite this paper)
        def score_citations(paper, depth, prob, edge_type="citation"):
            if depth >= max_depth or not paper.citations:
                return
            
            for cit in paper.citations:
                if cit.id in seen_papers:
                    continue
                seen_papers.add(cit.id)
                
                scores = self.score_paper_relevance(root_paper, cit)
                
                # Path probability decay (same as references)
                edge_prob = 0.8 if depth == 0 else 0.6
                current_prob = prob * edge_prob
                
                final_relevance = scores['combined_score'] * current_prob
                
                results.append({
                    "paper_id": cit.id,
                    "title": cit.title,
                    "depth": depth + 1,
                    "edge_type": "citation",  # cit cites this paper
                    "semantic_similarity": scores['semantic_similarity'],
                    "bibliographic_coupling": scores['bibliographic_coupling'],
                    "year_similarity": scores['year_similarity'],
                    "citation_score": scores['citation_score'],
                    "combined_score": scores['combined_score'],
                    "path_probability": current_prob,
                    "relevance_score": final_relevance
                })
                
                score_citations(cit, depth + 1, current_prob, edge_type)
        
        # Score both directions
        score_references(root_paper, 0, path_prob)
        score_citations(root_paper, 0, path_prob)
        
        return results


def compute_relevance_scores(
    root_paper, 
    max_depth: int = 2,
    use_cache: bool = True
) -> Tuple[List[Dict], RelevanceScorer]:
    """
    Convenience function to compute relevance scores for entire paper graph.
    
    Args:
        root_paper: Root paper with references and citations loaded
        max_depth: Maximum depth to traverse (applies to both references and citations)
        use_cache: Whether to cache embeddings
        
    Returns:
        Tuple of (scored results list, scorer instance)
    """
    scorer = RelevanceScorer(use_cache=use_cache)
    
    print("\nComputing relevance scores...")
    results = scorer.score_all_papers(
        root_paper,
        max_depth=max_depth
    )
    
    # Sort by final relevance score
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    
    return results, scorer