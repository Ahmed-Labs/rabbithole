import requests
import fitz
import io
from research_paper import ResearchPaper

API_URL = "https://api.semanticscholar.org/graph/v1"


def search(query, limit=50) -> list[ResearchPaper]:
    params = {
        "query": query,
        "limit": limit,
        "fields": "title,isOpenAccess,openAccessPdf,externalIds,url,authors,abstract",
    }

    url = f"{API_URL}/paper/search"
    resp = requests.get(url, params=params)
    resp.raise_for_status()

    results = resp.json().get("data", [])

    filtered = []
    for paper in results:
        pdf_url = None

        # openAccessPdf
        if paper.get("isOpenAccess") and paper.get("openAccessPdf", {}).get("url"):
            pdf_url = paper["openAccessPdf"]["url"]
        # arXiv
        elif "ArXiv" in paper.get("externalIds", {}):
            arxiv_id = paper["externalIds"]["ArXiv"]
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        if pdf_url:
            filtered.append(
                ResearchPaper(
                    id=paper.get("paperId"),
                    url=paper.get("url", ""),
                    title=paper.get("title", ""),
                    authors=paper.get("authors", []),
                    abstract=paper.get("abstract", ""),
                    pdf_url=pdf_url,
                )
            )
    return filtered


def fetch_pdf_text(pdf_url: str) -> str:
    resp = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())

    return "\n".join(text_chunks)
