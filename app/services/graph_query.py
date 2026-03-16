import heapq
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
    ) -> Tuple[
        dict[str, ResearchPaper],
        dict[str, ResearchPaper],
        List[RelevanceEdge],
        List[CitationEdge],
    ]:
        papers_by_id, relevance_edges, citation_edges = self.reader.read(
            paper_id, filters.max_depth
        )
        root_paper = papers_by_id.pop(paper_id, None)

        if root_paper is None:
            return {}, {}, [], []

        if not papers_by_id:
            return {paper_id: root_paper}, {}, [], []

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

        # Filtered papers only visible when on a path from an unfiltered paper *toward the root*.
        # 1) Distance from root (BFS both directions). 2) From each unfiltered node, traverse only to neighbors closer to root.
        valid_ids = filtered_ids | set(papers_by_id.keys())
        adj = defaultdict(set)
        for e in citation_edges:
            if e.src_id in valid_ids and e.dest_id in valid_ids:
                adj[e.src_id].add(e.dest_id)
                adj[e.dest_id].add(e.src_id)
        dist_from_root = {}
        frontier = {paper_id}
        d = 0
        while frontier:
            for n in frontier:
                dist_from_root[n] = d
            next_frontier = set()
            for n in frontier:
                for neighbor in adj.get(n, []):
                    if neighbor not in dist_from_root:
                        next_frontier.add(neighbor)
            frontier = next_frontier
            d += 1
        display_ids = set(filtered_ids)
        frontier = set(filtered_ids)
        while frontier:
            next_frontier = set()
            for n in frontier:
                my_d = dist_from_root.get(n, float("inf"))
                for neighbor in adj.get(n, []):
                    if neighbor in display_ids:
                        continue
                    neighbor_d = dist_from_root.get(neighbor, float("inf"))
                    if neighbor_d < my_d:  # only step toward root
                        display_ids.add(neighbor)
                        next_frontier.add(neighbor)
            frontier = next_frontier
        ghost_ids = display_ids - filtered_ids
        ghost_papers = {pid: papers_by_id[pid] for pid in ghost_ids if pid in papers_by_id}

        display_ids = filtered_ids | ghost_ids
        filtered_relevance = self._filter_by_paper_ids(relevance_edges, filtered_ids)
        display_citations = self._filter_by_paper_ids(citation_edges, display_ids)

        return filtered_papers, ghost_papers, filtered_relevance, display_citations

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

                selected = set(
                    heapq.nlargest(
                        k,
                        frontier,
                        key=lambda n: relevance.get(n, float("-inf")),
                    )
                )
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
