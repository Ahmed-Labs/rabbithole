# Pure LLM Scoring Explanation

## What You're Seeing

The **"Combined Relevance Score: 0.737"** you saw comes from **SPECTER2-based scoring**, which combines:
- Semantic Similarity (SPECTER2 embeddings)
- Bibliographic Coupling (shared references)
- Year Similarity
- Citation Score

This is **NOT** pure LLM scoring.

## Pure LLM Scoring

When you use **LLM scoring**, you get:
- ✅ **One prompt** that asks for both score AND explanation
- ✅ **Pure AI judgment** - no embeddings, no bibliographic analysis
- ✅ **Single similarity score** (0.0-1.0, equivalent to 1-10)
- ✅ **Explanation paragraph** explaining why papers are similar/different

## How the LLM Prompt Works

The LLM receives **one prompt** that asks for both:

```
Compare the following papers by providing a score from 1 to 10 on how similar 
they are and also provide a brief 1 paragraph explanation of how they are 
similar and different. Format the output so that the first line is just the 
similarity score and then on a new line output the explanation and do not say 
anything else.

PAPER 1:
[Title, Authors, Year, Abstract]

PAPER 2:
[Title, Authors, Year, Abstract]
```

The LLM responds with:
```
8.5 / 10

The two papers are highly similar because they share the same authors, cover 
the same research area...
```

This is parsed to extract:
- Score: 8.5/10 → 0.85 (converted to 0-1 scale)
- Explanation: The paragraph text

## How to Use Pure LLM Scoring

### Step 1: Set API Key
```powershell
$env:OPENAI_API_KEY="your-key-here"
```

### Step 2: Run Comparison
```bash
python compare_two_papers.py
```

### Step 3: Choose LLM Option
When asked "Use LLM for comparison?", choose **option 1** (LLM-based)

### Step 4: See Pure LLM Results
You'll see:
```
RESULTS (Pure LLM Scoring)
================================================================================

🎯 Similarity Score: 0.850 (on 0.0-1.0 scale)
   Equivalent to: 8.5/10

💡 Explanation:
   The two papers are highly similar because they share the same authors...
```

**No combined scores, no breakdowns - just pure LLM judgment!**

## Code Location

The pure LLM scoring happens in:
- `relevance_scoring/llm_scorer.py` → `LLMScorer.compute_score()`
- Uses **one prompt** that asks for both score and explanation
- Returns: `{"relevance_score": float, "explanation": str}`

## Key Differences

| Feature | SPECTER2 (Combined) | Pure LLM |
|---------|---------------------|----------|
| **Scoring Method** | Embeddings + bibliographic + year + citations | Pure AI judgment |
| **Output** | Multiple scores combined | Single similarity score |
| **Explanation** | No | Yes (from LLM) |
| **Prompt** | N/A (algorithmic) | Single prompt for score + explanation |
| **API Needed** | No | Yes |

## Summary

- **Combined Score (0.737)**: SPECTER2-based, multiple factors
- **Pure LLM Score**: Single AI judgment with explanation
- **One Prompt**: LLM gets one prompt asking for both score and explanation
- **To Use**: Set API key and choose LLM option when running `compare_two_papers.py`

