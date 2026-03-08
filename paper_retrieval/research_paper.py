from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import fitz

from paper_retrieval.session import session as r


@dataclass
class ResearchPaper:
    id: str
    url: str
    title: str
    authors: List[dict]
    abstract: str
    pdf_url: Optional[str] = None
    year: Optional[int] = None
    citation_count: Optional[int] = None
    # Papers this paper references
    references: List["ResearchPaper"] = field(default_factory=list)
    # Papers that cite this paper
    citations: List["ResearchPaper"] = field(default_factory=list)

    # Internal caches for full text
    _full_text_cache: Optional[str] = field(default=None, init=False, repr=False)
    _full_text_chunks_cache: Optional[List[str]] = field(
        default=None, init=False, repr=False
    )

    @property
    def full_text(self) -> Optional[str]:
        if self._full_text_cache is not None:
            return self._full_text_cache

        if not self.pdf_url:
            return None

        try:
            text = fetch_pdf_text(self.pdf_url)
            self._full_text_cache = text.strip()
        except Exception:
            pass

        return self._full_text_cache

    @property
    def full_text_chunks(self) -> List[str]:
        if self._full_text_chunks_cache is not None:
            return self._full_text_chunks_cache

        text = self.full_text
        if not text:
            return []

        self._full_text_chunks_cache = chunk_text_for_embedding(text)
        return self._full_text_chunks_cache

    @property
    def meta(self) -> str:
        return f"{self.title} {self.abstract}".strip()

    @property
    def bidirectional_citations(self) -> List[Tuple[str, str]]:
        """
        A list of citations represented by tuples of the form: (paper, cited_paper).
        This includes both the paper's citations and other papers that cite
        this paper.
        """
        out: List[Tuple[str, str]] = []
        out.extend((self.id, r.id) for r in self.references)
        out.extend((c.id, self.id) for c in self.citations)
        return out

    def to_props(self, nested_objects: bool = False) -> dict[str, Any]:
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "abstract": self.abstract,
            "pdf_url": self.pdf_url,
            "year": self.year,
            "citation_count": self.citation_count,
            "authors": [
                json.dumps(a) if isinstance(a, dict) else a
                for a in (self.authors or [])
            ] if not nested_objects else self.authors,
        }

    @classmethod
    def from_props(cls, d) -> ResearchPaper:
        return cls(
            id=d.get("id"),
            url=d.get("url", ""),
            title=d.get("title", ""),
            abstract=d.get("abstract", ""),
            pdf_url=d.get("pdf_url"),
            year=d.get("year"),
            citation_count=d.get("citation_count"),
            authors=[
                json.loads(a) if isinstance(a, str) else a for a in d.get("authors", [])
            ],
        )


# Global paper registry
PAPER_REGISTRY: dict[str, ResearchPaper] = {}


def new_research_paper(payload: dict) -> ResearchPaper:
    paper_id = payload.get("paperId")

    if paper_id in PAPER_REGISTRY:
        return PAPER_REGISTRY[paper_id]

    paper = ResearchPaper(
        id=paper_id,
        url=payload.get("url", ""),
        title=payload.get("title", ""),
        authors=payload.get("authors", []),
        abstract=payload.get("abstract", ""),
        pdf_url=extract_pdf_url(payload),
        year=payload.get("year"),
        citation_count=payload.get("citationCount"),
    )

    PAPER_REGISTRY[paper_id] = paper
    return paper


def extract_pdf_url(payload: dict) -> str:
    pdf_url = None
    external_ids = payload.get("externalIds") or {}

    if "ArXiv" in external_ids:
        arxiv_id = external_ids["ArXiv"]
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    elif payload.get("isOpenAccess") and payload.get("openAccessPdf", {}).get("url"):
        pdf_url = payload["openAccessPdf"]["url"]

    return pdf_url


def fetch_pdf_text(pdf_url: str) -> str:
    resp = r.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()

    pdf_bytes = io.BytesIO(resp.content)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text())

    return "\n".join(text_chunks)


def chunk_text_for_embedding(
    text: str,
    max_tokens: int = 512,
    approx_chars_per_token: int = 4,
) -> List[str]:
    if not text:
        return []

    max_chars = max_tokens * approx_chars_per_token  # ~2048 by default

    # Try to split on paragraph boundaries first
    paragraphs = text.split("\n\n")
    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for para in paragraphs:
        # +2 for the "\n\n" we'll reinsert
        para_len = len(para) + (2 if current else 0)

        if current_len + para_len <= max_chars:
            current.append(para)
            current_len += para_len
        else:
            # flush current chunk
            if current:
                chunks.append("\n\n".join(current))
            # start new chunk with this paragraph (may itself be long)
            if len(para) > max_chars:
                # hard-split overly-long paragraphs
                start = 0
                while start < len(para):
                    end = start + max_chars
                    chunks.append(para[start:end])
                    start = end
                current = []
                current_len = 0
            else:
                current = [para]
                current_len = len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks
