# How to Get Papers by Semantic Scholar ID

## Where to Find Semantic Scholar Paper IDs

### Method 1: From Semantic Scholar Website

1. **Go to**: https://www.semanticscholar.org/
2. **Search for a paper**
3. **Click on the paper**
4. **Look at the URL**:
   ```
   https://www.semanticscholar.org/paper/[PAPER-ID]/...
   ```
   
   Example:
   ```
   https://www.semanticscholar.org/paper/Attention-Is-All-You-Need-Vaswani-Shazeer/204e3073870fae3d05bcbc2f6a8e263d9a72c776
   ```
   
   The ID is the long alphanumeric string at the end: `204e3073870fae3d05bcbc2f6a8e263d9a72c776`

### Method 2: From Search Results (In Code)

When you search for papers, each paper has an `id` attribute:

```python
from paper_retrieval.paper_metadata import search

papers = search("machine learning transformers")
for paper in papers:
    print(f"Title: {paper.title}")
    print(f"ID: {paper.id}")  # This is the Semantic Scholar ID
    print()
```

### Method 3: From Paper Object

If you already have a paper object:
```python
paper_id = paper.id  # Get the ID from existing paper
```

---

## Existing Code to Get Papers

### Option 1: Search for Papers (Most Common)

```python
from paper_retrieval.paper_metadata import search

# Search and get papers
papers = search("your query here", limit=10)

# Each paper has an ID
paper = papers[0]
print(f"Paper ID: {paper.id}")
print(f"Title: {paper.title}")
```

### Option 2: Get Paper by ID (Already in compare_two_papers.py)

There's already a function in `compare_two_papers.py`:

```python
from compare_two_papers import get_paper_by_id

# Get paper by its Semantic Scholar ID
paper = get_paper_by_id("204e3073870fae3d05bcbc2f6a8e263d9a72c776")

if paper:
    print(f"Title: {paper.title}")
    print(f"Authors: {paper.authors}")
    print(f"Abstract: {paper.abstract}")
```

### Option 3: Use the Function Directly

The code is in `compare_two_papers.py`:

```python
def get_paper_by_id(paper_id: str) -> ResearchPaper:
    """Get a paper by its Semantic Scholar ID."""
    url = f"{API_URL}/paper/{paper_id}"
    params = {"fields": DEFAULT_FIELDS}
    
    try:
        resp = api_session.get(url, params=params)
        resp.raise_for_status()
        paper_data = resp.json()
        return new_research_paper(paper_data)
    except Exception as e:
        print(f"Error fetching paper: {e}")
        return None
```

---

## Adding a Helper Function to paper_metadata.py

I can add this function to `paper_metadata.py` so it's easier to use. Would you like me to do that?

---

## Complete Example

```python
from paper_retrieval.paper_metadata import search
from compare_two_papers import get_paper_by_id  # Or add to paper_metadata.py

# Method 1: Search and get ID
papers = search("attention is all you need")
paper1 = papers[0]
paper_id = paper1.id  # Get the ID
print(f"Paper ID: {paper_id}")

# Method 2: Use ID to get paper later
paper2 = get_paper_by_id(paper_id)
print(f"Retrieved: {paper2.title}")

# Method 3: Use ID from URL
# If you have: https://www.semanticscholar.org/paper/.../204e3073870fae3d05bcbc2f6a8e263d9a72c776
paper_id_from_url = "204e3073870fae3d05bcbc2f6a8e263d9a72c776"
paper3 = get_paper_by_id(paper_id_from_url)
```

---

## Quick Reference

**To get paper ID:**
- From search: `paper.id`
- From URL: Last part of Semantic Scholar URL
- From paper object: `paper.id`

**To get paper by ID:**
- Use `get_paper_by_id(paper_id)` from `compare_two_papers.py`
- Or search first, then use the paper object

