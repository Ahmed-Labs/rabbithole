import io
import fitz
from typing import Optional
from session import session as r
from research_paper import ResearchPaper, new_research_paper

API_URL = "https://api.semanticscholar.org/graph/v1"
DEFAULT_FIELDS = "title,isOpenAccess,openAccessPdf,externalIds,url,authors,abstract"


def extract_pdf_url(paper: dict) -> str:
    pdf_url = None
    external_ids = paper.get("externalIds") or {}

    if "ArXiv" in external_ids:
        arxiv_id = external_ids["ArXiv"]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif paper.get("isOpenAccess") and paper.get("openAccessPdf", {}).get("url"):
        pdf_url = paper["openAccessPdf"]["url"]

    return pdf_url


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
        paper_obj.pdf_url = extract_pdf_url(paper)
        if paper_obj.pdf_url:
            filtered.append(paper_obj)

    return filtered


def get_references(
    paper_id: str, limit: int = 100, max_results: Optional[int] = None
) -> list[ResearchPaper]:
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
            paper_obj.pdf_url = extract_pdf_url(paper)
            references.append(paper_obj)

            if max_results is not None and len(references) >= max_results:
                return references

        offset = data.get("next")
        if offset is None:
            break

    return references


def get_references_recur(
    paper: ResearchPaper, depth: int = 1, max_references: int = 10
):
    if depth <= 0:
        return

    paper.references = get_references(paper.id, max_results=max_references)
    for referenced_paper in paper.references:
        get_references_recur(referenced_paper, depth - 1)

    return paper


def fetch_pdf_text(pdf_url: str) -> str:
    resp = r.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())

    return "\n".join(text_chunks)
