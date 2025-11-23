"""
Example: How to get papers by ID or search.

This shows all the ways to obtain papers.
"""

from paper_retrieval.paper_metadata import search, get_paper_by_id

# ============================================
# METHOD 1: Search for papers (most common)
# ============================================

print("Method 1: Search for papers")
print("-" * 50)

papers = search("attention is all you need", limit=5)

for i, paper in enumerate(papers, 1):
    print(f"{i}. {paper.title[:60]}...")
    print(f"   ID: {paper.id}")
    print(f"   Year: {paper.year}")
    print()

# Get the first paper and its ID
if papers:
    paper1 = papers[0]
    paper_id = paper1.id
    print(f"Paper ID from search: {paper_id}")
    print()


# ============================================
# METHOD 2: Get paper by ID directly
# ============================================

print("\nMethod 2: Get paper by ID")
print("-" * 50)

# Example Semantic Scholar paper ID
# You can get this from:
# 1. The URL: https://www.semanticscholar.org/paper/.../204e3073870fae3d05bcbc2f6a8e263d9a72c776
# 2. From a paper object: paper.id
# 3. From search results above

example_id = "204e3073870fae3d05bcbc2f6a8e263d9a72c776"  # "Attention Is All You Need"

paper = get_paper_by_id(example_id)

if paper:
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join([a.get('name', '') for a in paper.authors[:3]])}")
    print(f"Year: {paper.year}")
    print(f"Abstract: {paper.abstract[:200]}...")
else:
    print("Paper not found or error occurred")
    print()


# ============================================
# METHOD 3: Get ID from existing paper
# ============================================

print("\nMethod 3: Get ID from existing paper object")
print("-" * 50)

# If you already have a paper object
papers = search("machine learning", limit=1)
if papers:
    existing_paper = papers[0]
    paper_id = existing_paper.id  # Extract the ID
    
    print(f"Original paper: {existing_paper.title}")
    print(f"Its ID: {paper_id}")
    
    # Use the ID to fetch it again later
    fetched_paper = get_paper_by_id(paper_id)
    if fetched_paper:
        print(f"Fetched again: {fetched_paper.title}")
        print("✓ Same paper!")


# ============================================
# WHERE TO FIND PAPER IDs
# ============================================

print("\n" + "=" * 50)
print("WHERE TO FIND SEMANTIC SCHOLAR PAPER IDs")
print("=" * 50)
print("""
1. From Semantic Scholar website:
   - Go to https://www.semanticscholar.org/
   - Search for a paper
   - Click on the paper
   - Look at the URL - the ID is the long string at the end
   - Example: .../paper/.../204e3073870fae3d05bcbc2f6a8e263d9a72c776

2. From search results (in code):
   - Use search() function
   - Each paper has a .id attribute
   - paper.id gives you the Semantic Scholar ID

3. From paper object:
   - If you have a ResearchPaper object
   - Access paper.id to get the ID

4. From API response:
   - When using Semantic Scholar API directly
   - The "paperId" field contains the ID
""")

