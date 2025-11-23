from typing import Optional
from paper_retrieval.session import session as r
from paper_retrieval.research_paper import ResearchPaper, new_research_paper

API_URL = "https://api.semanticscholar.org/graph/v1"
DEFAULT_FIELDS = "title,isOpenAccess,openAccessPdf,externalIds,url,authors,abstract,year,citationCount"


def search(query, limit=50) -> list[ResearchPaper]:
    params = {
        "query": query,
        "limit": limit,
        "fields": DEFAULT_FIELDS,
    }

    url = f"{API_URL}/paper/search"
    resp = r.get(url, params=params)
    resp.raise_for_status()

    results = resp.json().get("data", [])

    filtered = []
    for paper in results:
        paper_obj = new_research_paper(paper)
        if paper_obj.pdf_url:
            filtered.append(paper_obj)

    return filtered


def get_references(
    paper_id: str, limit: int = 100, max_results: Optional[int] = None
) -> list[ResearchPaper]:
    """Get papers that this paper cites (references)."""
    references = []
    offset = 0

    while True:
        if max_results is not None:
            remaining = max_results - len(references)
            if remaining <= 0:
                break
            page_limit = min(limit, remaining)
        else:
            page_limit = limit

        url = f"{API_URL}/paper/{paper_id}/references"
        params = {"fields": DEFAULT_FIELDS, "limit": page_limit, "offset": offset}
        resp = r.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data") or []
        for item in items:
            paper = item.get("citedPaper", {})
            if not paper:
                continue
            paper_obj = new_research_paper(paper)
            if paper_obj.pdf_url:
                references.append(paper_obj)

            if max_results is not None and len(references) >= max_results:
                return references

        offset = data.get("next")
        if offset is None:
            break

    return references


def get_citations(
    paper_id: str, limit: int = 100, max_results: Optional[int] = None
) -> list[ResearchPaper]:
    """Get papers that cite this paper (citations)."""
    citations = []
    offset = 0

    while True:
        if max_results is not None:
            remaining = max_results - len(citations)
            if remaining <= 0:
                break
            page_limit = min(limit, remaining)
        else:
            page_limit = limit

        url = f"{API_URL}/paper/{paper_id}/citations"
        params = {"fields": DEFAULT_FIELDS, "limit": page_limit, "offset": offset}
        resp = r.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data") or []
        for item in items:
            paper = item.get("citingPaper", {})
            if not paper:
                continue
            paper_obj = new_research_paper(paper)
            if paper_obj.pdf_url:
                citations.append(paper_obj)

            if max_results is not None and len(citations) >= max_results:
                return citations

        offset = data.get("next")
        if offset is None:
            break

    return citations


def get_references_recur(
    paper: ResearchPaper, depth: int = 1, max_references: int = 10
):
    """Recursively get references (papers this paper cites)."""
    if depth <= 0:
        return paper

    paper.references = get_references(paper.id, max_results=max_references)
    for referenced_paper in paper.references:
        get_references_recur(referenced_paper, depth - 1, max_references)

    return paper


def get_citations_recur(
    paper: ResearchPaper, depth: int = 1, max_citations: int = 10
):
    """Recursively get citations (papers that cite this paper)."""
    if depth <= 0:
        return paper

    paper.citations = paper.citations or get_citations(paper.id, max_results=max_citations)
    for citing_paper in paper.citations:
        get_citations_recur(citing_paper, depth - 1, max_citations)

    return paper


def build_full_graph(
    root_paper: ResearchPaper,
    depth: int = 1,
    max_per_level: int = 10,
    include_citations: bool = True
) -> ResearchPaper:
    """
    Build a complete graph with both references and citations.
    
    Args:
        root_paper: The root paper to expand from
        depth: How many levels to fetch (applies to both references and citations)
        max_per_level: Max papers per level (applies to both references and citations)
        include_citations: Whether to fetch citations in addition to references
        
    Returns:
        Root paper with both references and citations populated
    """
    print(f"Fetching references (depth={depth}, max={max_per_level})...")
    get_references_recur(root_paper, depth=depth, max_references=max_per_level)
    
    if include_citations:
        print(f"Fetching citations (depth={depth}, max={max_per_level})...")
        get_citations_recur(root_paper, depth=depth, max_citations=max_per_level)
    
    return root_paper


def get_paper_by_id(paper_id: str) -> Optional[ResearchPaper]:
    """
    Get a paper by its Semantic Scholar paper ID.
    
    Args:
        paper_id: Semantic Scholar paper ID (e.g., "204e3073870fae3d05bcbc2f6a8e263d9a72c776")
    
    Returns:
        ResearchPaper object if found, None otherwise
    
    Example:
        paper = get_paper_by_id("204e3073870fae3d05bcbc2f6a8e263d9a72c776")
    """
    url = f"{API_URL}/paper/{paper_id}"
    params = {"fields": DEFAULT_FIELDS}
    
    try:
        resp = r.get(url, params=params)
        resp.raise_for_status()
        paper_data = resp.json()
        return new_research_paper(paper_data)
    except Exception as e:
        print(f"Error fetching paper {paper_id}: {e}")
        return None


def fetch_pdf_text(pdf_url: str) -> str:
    resp = r.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())

    return "\n".join(text_chunks)