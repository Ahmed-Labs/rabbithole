from dataclasses import dataclass
from typing import List, Optional, Tuple

from db.reader import KnowledgeGraphReader
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge


@dataclass
class GraphFilters:
    max_depth: int = 3
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_citations: Optional[int] = None
    min_relevance: Optional[float] = None


class GraphQueryService:
    """Business logic for graph queries with filtering and aggregation."""

    def __init__(self, reader: KnowledgeGraphReader):
        self.reader = reader

    def get_filtered_graph(
        self, paper_id: str, filters: GraphFilters
    ) -> Tuple[dict[str, ResearchPaper], List[RelevanceEdge], List[CitationEdge]]:
        papers_by_id, relevance_edges, citation_edges = self.reader.read(
            paper_id, filters.max_depth
        )
        root_paper = papers_by_id.pop(paper_id, None)

        if not papers_by_id or root_paper is None:
            return [], [], []

        filtered_papers = {
            pid: p
            for pid, p in papers_by_id.items()
            if self._passes_filters(p, filters)
        }

        if filters.min_relevance is not None:
            for e in relevance_edges:
                pid = e.dest_id if e.src_id == paper_id else e.src_id
                if e.relevance_score.combined < filters.min_relevance:
                    filtered_papers.pop(pid, None)

        filtered_papers[root_paper.id] = root_paper
        filtered_ids = set(filtered_papers.keys())

        filtered_relevance = self._filter_by_paper_ids(relevance_edges, filtered_ids)
        filtered_citations = self._filter_by_paper_ids(citation_edges, filtered_ids)

        return filtered_papers, filtered_relevance, filtered_citations

    def _passes_filters(self, p: ResearchPaper, filters: GraphFilters) -> bool:
        return (
            (filters.min_year is None or p.year >= filters.min_year)
            and (filters.max_year is None or p.year <= filters.max_year)
            and (
                filters.min_citations is None
                or p.citation_count >= filters.min_citations
            )
        )

    def _filter_by_paper_ids(self, edges: List, valid_ids: set[str]) -> List:
        return [e for e in edges if e.src_id in valid_ids and e.dest_id in valid_ids]
