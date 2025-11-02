# SPECTER2 Quick Reference

## Installation (One Command)

```bash
pip install transformers adapters torch scikit-learn numpy
```

## Test It Works

```bash
python semantic_similarity/compare_embedding_models.py
```

## Run Full Pipeline

```bash
python visualize_with_relevance.py
```

## What You Get

### Output Files
- `output/references_graph_specter2.html` - Interactive visualization
- `output/relevance_scores_specter2.csv` - All scores in CSV
- `.embedding_cache/` - Cached embeddings (speed boost)

### Console Output
```
TOP 15 MOST RELEVANT PAPERS (SPECTER2 + ConnectedPapers-style scoring)

1. Paper Title Here
   └─ Relevance: 0.6800
      ├─ Semantic (SPECTER2): 0.8500
      ├─ Bib. Coupling: 0.1200
      ├─ Year Similarity: 0.9500
      ├─ Citation Score: 0.7000
      └─ Path Probability: 0.8000 (depth: 1)
```

## Understanding the Scores

| Score | Range | Meaning |
|-------|-------|---------|
| **Relevance** | 0-1 | Final combined score (this is what you care about) |
| **Semantic** | 0-1 | How similar the paper content is (SPECTER2 embeddings) |
| **Bib. Coupling** | 0-1 | Ratio of shared references (ConnectedPapers method) |
| **Year Similarity** | 0-1 | How close in publication year (1.0 = same year) |
| **Citation Score** | 0-1 | Normalized citation count (more = better) |
| **Path Probability** | 0-1 | Distance in citation chain (0.8 = direct, 0.48 = 2nd level) |

## Formula

```python
combined_score = (
    0.70 * semantic_similarity +
    0.15 * bibliographic_coupling +
    0.10 * year_similarity +
    0.05 * citation_score
)

relevance_score = combined_score * path_probability
```

## Customize Query

Edit `visualize_with_relevance.py`:

```python
query = "your search here"  # Line ~122
max_depth = 2              # How many citation levels (1-3)
max_references = 10        # Papers per level (5-20)
```

## Tuning Weights

Edit `semantic_similarity/relevance_scorer.py`, line ~210:

```python
combined = (
    0.70 * semantic_sim +      # ← Increase if content matters most
    0.15 * bib_coupling +      # ← Increase if shared refs matter
    0.10 * year_sim +          # ← Increase if recency matters
    0.05 * citation_score      # ← Increase if popularity matters
)
```

## Cache Management

```bash
# Clear cache (forces re-computation)
rm -rf .embedding_cache/

# Check cache size
du -sh .embedding_cache/
```

## GPU vs CPU

```python
# Force CPU (if GPU issues)
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Check what's being used
import torch
print(f"Using: {'GPU' if torch.cuda.is_available() else 'CPU'}")
```

## Common Adjustments

### Get More Papers
```python
max_references = 20  # Default: 10
```

### Go Deeper
```python
max_depth = 3  # Default: 2 (warning: exponential growth!)
```

### Different Search
```python
query = "machine learning transformers"
```

### Prioritize Recent Papers
```python
# In relevance_scorer.py, line ~210
combined = (
    0.60 * semantic_sim +
    0.10 * bib_coupling +
    0.25 * year_sim +        # ← Increased from 0.10
    0.05 * citation_score
)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: adapters` | `pip install adapters` |
| Out of memory | Use CPU: `os.environ['CUDA_VISIBLE_DEVICES'] = ''` |
| Slow first run | Normal! Downloading 450MB model |
| All scores are low | Check if abstracts are available |
| Can't find papers | Try different search query |

## Performance

- **First run**: 2-5 minutes (model download)
- **With cache**: 30-60 seconds
- **Per paper**: ~0.1s (GPU) or ~1s (CPU)

## Files You Care About

- ✏️ **`visualize_with_relevance.py`** - Main script (change query here)
- 🧠 **`semantic_similarity/relevance_scorer.py`** - Scoring logic (change weights here)
- 📊 **`output/references_graph_specter2.html`** - Open in browser
- 📄 **`output/relevance_scores_specter2.csv`** - Import to Excel/Python

## That's It!

Everything else is just documentation. Start with:

```bash
python visualize_with_relevance.py
```

Then open `output/references_graph_specter2.html` in your browser.