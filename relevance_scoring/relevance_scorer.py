from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
import numpy as np

from relevance_scoring.embedder import Embedder
from paper_retrieval import ResearchPaper


@dataclass
class RelevanceScore:
    semantic_similarity: float
    year_similarity: float
    citation_score: float
    llm_explanation: Optional[str] = None  # Optional explanation from LLM
    llm_semantic_score: Optional[float] = None  # Optional LLM-based semantic score

    @property
    def combined(self):
        # Use LLM semantic score if available, otherwise use embedding-based
        semantic = self.llm_semantic_score if self.llm_semantic_score is not None else self.semantic_similarity
        return (
            0.75 * self.semantic_similarity
            + 0.15 * self.year_similarity
            + 0.10 * self.citation_score
        )


@dataclass
class RelevanceEdge:
    src_id: str
    dest_id: str
    relevance_score: RelevanceScore
    edge_type: str = "reference"  # "reference" or "citation"
    depth: int = 1


class RelevanceScorer:
    """
    Compute semantic relevance scores between papers.

    Relevance scores consist of:
    - Semantic similarity (SPECTER2 embeddings or LLM-based)
    - Co-citation analysis (papers cited together)
    - Publication year proximity
    
    Can optionally use LLM for semantic scoring and explanations.
    """

    def __init__(self):
        self.embedder = Embedder()

    def _compute_year_similarity(
        self, year1: Optional[int], year2: Optional[int]
    ) -> float:
        """
        Compute year proximity score (ConnectedPapers prioritizes similar generations).
        Returns 1.0 for same year, decaying with distance.
        """
        if year1 is None or year2 is None:
            return 0.5  # neutral if year unknown

        year_diff = abs(year1 - year2)

        # Decay function: 1.0 at 0 years, 0.5 at 5 years, ~0.2 at 10 years
        return np.exp(-year_diff / 5.0)

    def _get_citation_score(self, paper) -> float:
        """
        Normalize citation count to 0-1 range.
        More citations = potentially more important paper.
        """
        if not hasattr(paper, "citation_count") or paper.citation_count is None:
            return 0.5

        # Log scale normalization (most papers have 0-1000 citations)
        # Score: 0.5 at 100 citations, ~0.7 at 1000 citations
        return min(0.5 + np.log10(paper.citation_count + 1) / 6, 1.0)

    def _compute_semantic_similarity(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> float:
        root_embs = self.embedder.lazy_embed_chunks(
            lambda: root_paper.full_text_chunks, cache_key=root_paper.id + ":text"
        )
        target_embs = self.embedder.lazy_embed_chunks(
            lambda: target_paper.full_text_chunks, cache_key=target_paper.id + ":text"
        )

        full_text_sim = self.embedder.compute_similarity(root_embs, target_embs)

        root_meta_emb = self.embedder.embed(root_paper.meta, root_paper.id + ":meta")
        target_meta_emb = self.embedder.embed(
            target_paper.meta, target_paper.id + ":meta"
        )
        meta_sim = self.embedder.compute_similarity(root_meta_emb, target_meta_emb)
        return 0.8 * full_text_sim + 0.2 * meta_sim

    def compute_score(
        self, root_paper: ResearchPaper, target_paper: ResearchPaper
    ) -> Optional[RelevanceScore]:
        return RelevanceScore(
            semantic_similarity=self._compute_semantic_similarity(
                root_paper, target_paper
            ),
            year_similarity=self._compute_year_similarity(
                root_paper.year, target_paper.year
            ),
            citation_score=self._get_citation_score(target_paper),
        )

    def compute_relevance_edges(
        self,
        root_paper: ResearchPaper,
    ) -> List[RelevanceEdge]:
        """
        Recursively score all papers in reference tree against root paper.
        """
        edges: List[RelevanceEdge] = []

        visited: Set[str] = set()
        scored: Set[str] = set()

        def dfs(paper: ResearchPaper):
            if paper.id in visited:
                return
            visited.add(paper.id)

            adjacent_papers = paper.references + paper.citations
            if not adjacent_papers:
                return

            for adj in adjacent_papers:
                if adj.id not in scored:
                    score = self.compute_score(root_paper, adj)
                    if score:
                        edges.append(
                            RelevanceEdge(
                                src_id=root_paper.id,
                                dest_id=adj.id,
                                relevance_score=score,
                            )
                        )
                    scored.add(adj.id)

                dfs(adj)

        dfs(root_paper)
        return edges


def compute_relevance_scores(
    root_paper,
    use_llm: bool = False,
    llm_scorer=None,
    max_depth: Optional[int] = None,
    use_cache: bool = True
) -> Tuple[List[dict], RelevanceScorer]:
    """
    Compute relevance scores for all papers in the graph.
    
    Args:
        root_paper: The root paper to score against
        use_llm: Whether to use LLM for semantic scoring
        llm_scorer: Optional LLMScorer instance (created if use_llm=True and None)
        max_depth: Optional max depth (currently unused, kept for compatibility)
        use_cache: Whether to use embedding cache (currently unused, kept for compatibility)
    
    Returns:
        Tuple of (results_list, scorer) where results_list is a list of dicts with:
        - paper_id: str
        - title: str
        - relevance_score: float
        - semantic_similarity: float
        - bibliographic_coupling: float
        - year_similarity: float
        - citation_score: float
        - llm_explanation: Optional[str]
        - edge_type: str ("reference" or "citation")
        - depth: int
        - path_probability: float (placeholder, currently 1.0)
    """
    scorer = RelevanceScorer(use_llm=use_llm, llm_scorer=llm_scorer)

    print("\nComputing relevance scores...")
    if use_llm:
        print("Using LLM for semantic scoring and explanations...")
    edges = scorer.compute_relevance_edges(root_paper)

    edges.sort(key=lambda x: x.relevance_score.combined, reverse=True)

    # Convert edges to dictionary format expected by visualization
    results = []
    paper_map = {}  # Map paper IDs to paper objects for title lookup
    
    def collect_papers(paper, depth=0):
        """Recursively collect all papers in the graph."""
        if paper.id not in paper_map:
            paper_map[paper.id] = paper
        for ref in paper.references:
            if ref.id not in paper_map:
                paper_map[ref.id] = ref
                collect_papers(ref, depth + 1)
        for cit in paper.citations:
            if cit.id not in paper_map:
                paper_map[cit.id] = cit
                collect_papers(cit, depth + 1)
    
    collect_papers(root_paper)
    
    for edge in edges:
        target_paper = paper_map.get(edge.dest_id)
        if not target_paper:
            continue
        
        result = {
            "paper_id": edge.dest_id,
            "title": target_paper.title if target_paper else "Unknown",
            "relevance_score": edge.relevance_score.combined,
            "semantic_similarity": edge.relevance_score.semantic_similarity,
            "bibliographic_coupling": edge.relevance_score.bibliographic_coupling,
            "year_similarity": edge.relevance_score.year_similarity,
            "citation_score": edge.relevance_score.citation_score,
            "llm_explanation": edge.relevance_score.llm_explanation,
            "edge_type": edge.edge_type,
            "depth": edge.depth,
            "path_probability": 1.0,  # Placeholder
        }
        results.append(result)

    return results, scorer
