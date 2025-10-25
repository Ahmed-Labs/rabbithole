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


def new_research_paper(payload: dict) -> ResearchPaper:
    return ResearchPaper(
        id=payload.get("paperId"),
        url=payload.get("url", ""),
        title=payload.get("title", ""),
        authors=payload.get("authors", []),
        abstract=payload.get("abstract", ""),
    )
