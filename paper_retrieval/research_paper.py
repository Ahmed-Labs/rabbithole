from dataclasses import dataclass


@dataclass
class ResearchPaper:
    id: str
    url: str
    title: str
    authors: list[dict]
    abstract: str
    pdf_url: str
