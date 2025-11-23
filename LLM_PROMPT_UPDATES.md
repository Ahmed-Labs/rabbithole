# LLM Prompt Updates Based on Testing

## Summary of Changes

The LLM scorer has been updated to match your tested prompt format that showed good results with ChatGPT and Gemini.

## Key Changes

### 1. Score Scale: Changed from 0.0-1.0 to 1-10

**Before:**
- Prompt asked for score from 0.0 to 1.0
- Direct JSON response

**After:**
- Prompt asks for score from 1 to 10 (matches your tested format)
- System automatically converts 1-10 scale to 0-1 scale internally
- Example: 8.5/10 → 0.85 internally

### 2. Output Format: Matches Your Tested Format

**Your tested format:**
```
8.5 / 10

[Explanation paragraph]
```

**Implementation:**
- First line: Just the score (e.g., "8.5 / 10" or "7/10")
- Second line: Brief paragraph explanation
- No extra text or formatting

### 3. Prompt Text: Matches Your Successful Prompts

**New prompt:**
```
Compare the following papers by providing a score from 1 to 10 on how similar they are and also provide a brief 1 paragraph explanation of how they are similar and different. Format the output so that the first line is just the similarity score and then on a new line output the explanation and do not say anything else.

PAPER 1:
[Title, Authors, Year, Abstract]

PAPER 2:
[Title, Authors, Year, Abstract]
```

This matches your tested prompts that produced:
- **Test 1 (Very similar)**: 8.5/10 - "highly similar because they share the same authors, cover the same research area..."
- **Test 2 (Quite similar)**: 7/10 - "reasonably similar because both focus on science mapping..."
- **Test 3 (Barely similar)**: 1/10 - "almost entirely dissimilar in scope, purpose, methodology..."

### 4. Response Parsing

The system now parses responses in the format:
- Extracts score from first line (handles "8.5 / 10", "7/10", or just "7")
- Extracts explanation from remaining lines
- Converts 1-10 scale to 0-1 scale for internal use
- Handles variations in formatting

## How Papers Are Obtained

### Current Implementation

Papers are retrieved from **Semantic Scholar API** with the following information:

1. **Search API** (`paper/search`):
   - Title
   - Authors (list with names)
   - Abstract
   - Year
   - Citation count
   - PDF URL (if available)

2. **Citation Graph API**:
   - References (papers this paper cites)
   - Citations (papers that cite this paper)

3. **What's Provided to LLM**:
   ```
   Title: [Paper Title]
   Authors: [Author names]
   Year: [Publication year]
   Abstract: [Paper abstract (truncated to 1000 chars)]
   Citations: [Citation count]
   ```

### Why This Works

Your testing showed that **title, abstract, authors, and year are sufficient** for accurate similarity scoring:

- ✅ **Test 1 (8.5/10)**: LLM correctly identified same authors, same research area, same workflow
- ✅ **Test 2 (7/10)**: LLM identified shared concepts (science mapping, bibliometric methods)
- ✅ **Test 3 (1/10)**: LLM correctly identified completely different domains

The abstract contains enough information about:
- Research topics and themes
- Methodologies used
- Research questions addressed
- Domain and conceptual overlap

## Usage Example

```python
from relevance_scoring import LLMScorer, compute_relevance_scores
from paper_retrieval.paper_metadata import search, build_full_graph

# Get papers from Semantic Scholar
papers = search("science mapping tools")
root_paper = papers[0]

# Build citation graph
root_paper = build_full_graph(root_paper, depth=1, max_per_level=5)

# Score with LLM (uses your tested prompt format)
llm_scorer = LLMScorer(
    provider="openai",  # or "anthropic" for Gemini
    model="gpt-4o-mini",
    use_explanations=True
)

results, scorer = compute_relevance_scores(
    root_paper,
    use_llm=True,
    llm_scorer=llm_scorer
)

# Results will have:
# - relevance_score: 0.0-1.0 (converted from 1-10)
# - llm_explanation: Brief paragraph explanation
# - semantic_similarity: LLM score (0.0-1.0)
```

## Expected Output Format

When you run the LLM scorer, it will:

1. **Send prompt** matching your tested format
2. **Receive response** like:
   ```
   8.5 / 10
   
   The two papers are highly similar because they share the same authors...
   ```

3. **Parse and convert**:
   - Extract: 8.5/10 → 0.85
   - Extract: Explanation text
   - Store in RelevanceScore object

4. **Display in results**:
   - Console: Shows explanation with 💡 icon
   - CSV: Includes `llm_explanation` column
   - Graph: Shows explanation in tooltips

## Testing Results Reference

Based on your testing:

| Comparison | Expected Score | Actual (ChatGPT) | Actual (Gemini) |
|------------|---------------|-------------------|-----------------|
| Paper 1 vs Paper 2 (same network, top match) | Very similar | 8.5/10 | 9/10 |
| Paper 1 vs Paper 3 (same network, further) | Quite similar | 7/10 | 7/10 |
| Paper 1 vs Paper 4 (different network) | Barely similar | 1/10 | 2/10 |

The implementation now uses the same prompt format that produced these results.

## Notes

- **Score conversion**: Internal system uses 0.0-1.0 scale, but LLM uses 1-10 scale (as tested)
- **Explanation length**: Brief, single paragraph (as in your tests)
- **Paper information**: Uses title, abstract, authors, year (sufficient based on testing)
- **Format consistency**: Matches your tested format exactly

