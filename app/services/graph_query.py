from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional, Tuple

from db.reader import KnowledgeGraphReader
from paper_retrieval.research_paper import ResearchPaper
from relevance_scoring.relevance_scorer import CitationEdge, RelevanceEdge

TOP_K_PAPERS = 20


@dataclass
class GraphFilters:
    max_depth: int = 3
    min_year: Optional[int] = None
    max_year: Optional[int] = None
    min_citations: Optional[int] = None
    min_relevance: Optional[float] = None


class GraphQueryService:
    def __init__(self, reader: KnowledgeGraphReader):
        self.reader = reader

    def get_filtered_graph(
        self, paper_id: str, filters: GraphFilters
    ) -> Tuple[dict[str, ResearchPaper], List[RelevanceEdge], List[CitationEdge]]:
        papers_by_id, relevance_edges, citation_edges = self.reader.read(
            paper_id, filters.max_depth
        )
        root_paper = papers_by_id.pop(paper_id, None)

        if root_paper is None:
            return {}, [], []

        if not papers_by_id:
            return {paper_id: root_paper}, [], []

        top_papers = self._top_k(
            paper_id,
            citation_edges,
            relevance_edges,
            filters.max_depth,
            TOP_K_PAPERS,
        )

        filtered_papers = {
            pid: p
            for pid, p in papers_by_id.items()
            if self._passes_filters(p, filters) and pid in top_papers
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

    def _top_k(
        self,
        root_id: str,
        citation_edges: list[CitationEdge],
        relevance_edges: list[RelevanceEdge],
        max_depth: int,
        k: int,
    ) -> set[str]:
        # Adjacency list for both outgoing and incoming citation edges
        out_adj = defaultdict(set)
        in_adj = defaultdict(set)

        for e in citation_edges:
            out_adj[e.src_id].add(e.dest_id)
            in_adj[e.dest_id].add(e.src_id)

        relevance = {}
        for e in relevance_edges:
            other = e.dest_id if e.src_id == root_id else e.src_id
            relevance[other] = e.relevance_score.combined

        def bfs(seeds, adj):
            kept = set()
            frontier = set(seeds)

            for _ in range(1, max_depth + 1):
                if not frontier:
                    break

                ranked = sorted(
                    frontier,
                    key=lambda n: relevance.get(n, float("-inf")),
                    reverse=True,
                )

                selected = set(ranked[:k])
                kept |= selected

                nxt = set()
                for u in selected:
                    nxt.update(adj.get(u, []))

                frontier = nxt - kept

            return kept

        out_seeds = out_adj.get(root_id, set())
        in_seeds = in_adj.get(root_id, set())

        # Applies top k to both incoming/outgoing citation subgraphs
        out_nodes = bfs(out_seeds, out_adj)
        in_nodes = bfs(in_seeds, in_adj)

        return {root_id} | out_nodes | in_nodes
