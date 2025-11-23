# Paper Retrieval Documentation

## How Papers Are Obtained

The repository uses the **Semantic Scholar API** to retrieve research papers. Here's how it works:

### 1. Paper Search

Papers are initially retrieved via the Semantic Scholar search API:

```python
from paper_retrieval.paper_metadata import search

papers = search("antioxidants", limit=50)
```

**What's retrieved:**
- Paper ID (Semantic Scholar ID)
- Title
- Authors (list of author dictionaries with names)
- Abstract
- Publication year
- Citation count
- URL
- PDF URL (if available - ArXiv or open access)
- External IDs (ArXiv ID, etc.)

**API Endpoint:** `https://api.semanticscholar.org/graph/v1/paper/search`

**Fields retrieved:** `title,isOpenAccess,openAccessPdf,externalIds,url,authors,abstract,year,citationCount`

### 2. Building Citation Graphs

Once you have a root paper, the system can build citation graphs:

#### References (Papers the root paper cites)
```python
from paper_retrieval.paper_metadata import get_references

references = get_references(paper_id, max_results=10)
```

#### Citations (Papers that cite the root paper)
```python
from paper_retrieval.paper_metadata import get_citations

citations = get_citations(paper_id, max_results=10)
```

#### Recursive Graph Building
```python
from paper_retrieval.paper_metadata import build_full_graph

# Build graph with references and citations, recursively
root_paper = build_full_graph(
    root_paper,
    depth=2,              # How many levels deep
    max_per_level=10,     # Max papers per level
    include_citations=True  # Include both references and citations
)
```

### 3. What Information Is Available

For each paper, the `ResearchPaper` dataclass contains:

```python
@dataclass
class ResearchPaper:
    id: str                    # Semantic Scholar paper ID
    url: str                   # Paper URL on Semantic Scholar
    title: str                 # Paper title
    authors: List[dict]        # List of author dicts with names
    abstract: str              # Paper abstract
    pdf_url: Optional[str]     # Direct PDF URL (if available)
    references: List[ResearchPaper]  # Papers this paper cites
    citations: List[ResearchPaper]    # Papers that cite this paper
    year: Optional[int]        # Publication year
    citation_count: Optional[int]  # Number of citations
```

### 4. PDF Text Extraction (Optional)

If you need the full text of a paper:

```python
from paper_retrieval.paper_metadata import fetch_pdf_text

text = fetch_pdf_text(pdf_url)  # Extracts text from PDF using PyMuPDF
```

**Note:** This requires the paper to have an accessible PDF URL (ArXiv or open access).

### 5. Limitations

**What's NOT retrieved:**
- Full paper text (only abstract is available via API)
- Paper content beyond title/abstract (unless PDF is fetched separately)
- Full author affiliations
- Keywords (unless in abstract)
- Full reference lists (only paper IDs)

**API Limitations:**
- Semantic Scholar API has rate limits (free tier: 100 requests per 5 minutes)
- Not all papers have PDFs available
- Some papers may have incomplete metadata

### 6. Current LLM Scoring Input

When using LLM-based scoring, the system currently provides the LLM with:

```
Title: [Paper Title]
Authors: [Author names]
Year: [Publication year]
Abstract: [Paper abstract (truncated to 1000 chars)]
Citations: [Citation count]
```

**This is sufficient for most similarity comparisons**, as LLMs can effectively compare papers based on:
- Research topics (from title and abstract)
- Methodologies (from abstract)
- Domain overlap (from abstract)
- Temporal context (from year)
- Author overlap (from authors list)

### 7. Enhancing Paper Information

If you need more information for LLM scoring, you could:

1. **Fetch PDF text** (if available):
   ```python
   if paper.pdf_url:
       full_text = fetch_pdf_text(paper.pdf_url)
       # Use full_text in LLM prompt
   ```

2. **Extract keywords** from abstract (using NLP libraries)

3. **Get more metadata** from Semantic Scholar API (requires expanding `DEFAULT_FIELDS`)

4. **Use paper references** to understand context:
   ```python
   # Include information about what papers this paper cites
   ref_titles = [ref.title for ref in paper.references[:5]]
   ```

### 8. Example: Complete Paper Retrieval Workflow

```python
from paper_retrieval.paper_metadata import search, build_full_graph
from relevance_scoring import LLMScorer, compute_relevance_scores

# 1. Search for papers
papers = search("science mapping tools", limit=10)

# 2. Select root paper
root_paper = papers[0]

# 3. Build citation graph
root_paper = build_full_graph(
    root_paper,
    depth=2,
    max_per_level=10,
    include_citations=True
)

# 4. Score with LLM (uses title, authors, abstract, year)
llm_scorer = LLMScorer(provider="openai", use_explanations=True)
results, scorer = compute_relevance_scores(
    root_paper,
    use_llm=True,
    llm_scorer=llm_scorer
)

# Each result contains:
# - Paper title, abstract, authors, year (from Semantic Scholar)
# - LLM-generated similarity score and explanation
```

## Summary

**Papers are obtained from Semantic Scholar API** which provides:
- ✅ Title, authors, abstract, year, citation count
- ✅ Citation relationships (references and citations)
- ✅ PDF URLs (when available)

**For LLM scoring**, this metadata is sufficient because:
- LLMs excel at understanding semantic similarity from abstracts
- Title and abstract capture the core research contribution
- Author and year provide additional context

The current implementation matches your tested format where LLMs successfully compared papers using just title, abstract, authors, and year information.

