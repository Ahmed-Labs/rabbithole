from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class ResearchPaper:
    id: str
    url: str
    title: str
    authors: List[dict]
    abstract: str
    pdf_url: Optional[str] = None
    references: List["ResearchPaper"] = field(default_factory=list)
    year: Optional[int] = None
    citation_count: Optional[int] = None


def new_research_paper(payload: dict) -> ResearchPaper:
    return ResearchPaper(
        id=payload.get("paperId"),
        url=payload.get("url", ""),
        title=payload.get("title", ""),
        authors=payload.get("authors", []),
        abstract=payload.get("abstract", ""),
        pdf_url=extract_pdf_url(payload),
        year=payload.get("year"),
        citation_count=payload.get("citationCount")
    )

def extract_pdf_url(payload: dict) -> str:
    pdf_url = None
    external_ids = payload.get("externalIds") or {}

    if "ArXiv" in external_ids:
        arxiv_id = external_ids["ArXiv"]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif payload.get("isOpenAccess") and payload.get("openAccessPdf", {}).get("url"):
        pdf_url = payload["openAccessPdf"]["url"]

    return pdf_url