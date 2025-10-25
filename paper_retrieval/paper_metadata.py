import io
import fitz
from session import session as r
from research_paper import ResearchPaper, new_research_paper

API_URL = "https://api.semanticscholar.org/graph/v1"
DEFAULT_FIELDS = "title,isOpenAccess,openAccessPdf,externalIds,url,authors,abstract"


def extract_pdf_url(paper: dict) -> str:
    pdf_url = None
    # arXiv
    if "ArXiv" in paper.get("externalIds", {}):
        arxiv_id = paper["externalIds"]["ArXiv"]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    # openAccessPdf
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

def get_citations(paper_id: str, limit: int = 10) -> list[ResearchPaper]:
    citations = []
    offset = 0

    while True:
        url = f"{API_URL}/paper/{paper_id}/citations"
        params = {"fields": DEFAULT_FIELDS, "limit": limit, "offset": offset}
        resp = r.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("data", []):
            paper = item.get("citingPaper", {})
            if not paper:
                continue
            paper_obj = new_research_paper(paper)
            paper_obj.pdf_url = extract_pdf_url(paper)

            if paper_obj.pdf_url:
                citations.append(paper_obj)

        next_offset = data.get("next")
        if not next_offset:
            break
        offset = next_offset

    return citations

def fetch_pdf_text(pdf_url: str) -> str:
    resp = r.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())

    return "\n".join(text_chunks)
