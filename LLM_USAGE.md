# LLM-Based Relevance Scoring Guide

This repository now supports optional LLM-based relevance scoring with natural language explanations.

## Features

- **LLM-based semantic scoring**: Use GPT-4, Claude, or other LLMs to compute semantic similarity
- **Natural language explanations**: Get human-readable explanations of why papers are similar
- **Multiple provider support**: OpenAI, Anthropic, or HuggingFace models
- **Optional integration**: Works alongside or instead of SPECTER2 embeddings

## Quick Start

### 1. Install LLM Dependencies

Choose one or more providers:

```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic

# For HuggingFace (already installed if using transformers)
# No additional install needed
```

### 2. Set API Keys

```bash
# For OpenAI
export OPENAI_API_KEY="your-key-here"

# For Anthropic
export ANTHROPIC_API_KEY="your-key-here"
```

### 3. Use LLM Scoring

#### Option A: Modify existing script

Edit `experiments/visualize_relevance_scores.py`:

```python
# Change this line (around line 227)
use_llm = True  # Change from False to True

# Optionally customize LLM settings
from relevance_scoring import LLMScorer
llm_scorer = LLMScorer(
    provider="openai",  # or "anthropic"
    model="gpt-4o-mini",  # Cost-effective default
    use_explanations=True
)
```

#### Option B: Use dedicated LLM script

```bash
python experiments/visualize_with_llm.py
```

## Configuration Options

### LLM Provider Selection

```python
from relevance_scoring import LLMScorer

# OpenAI (recommended for cost-effectiveness)
llm_scorer = LLMScorer(
    provider="openai",
    model="gpt-4o-mini",  # or "gpt-4", "gpt-3.5-turbo"
    use_explanations=True
)

# Anthropic Claude
llm_scorer = LLMScorer(
    provider="anthropic",
    model="claude-3-haiku-20240307",  # Fast and cost-effective
    use_explanations=True
)

# HuggingFace (local, no API needed)
llm_scorer = LLMScorer(
    provider="huggingface",
    model="meta-llama/Llama-2-7b-chat-hf",  # Requires GPU
    use_explanations=True
)
```

### Using LLM in RelevanceScorer

```python
from relevance_scoring import RelevanceScorer, LLMScorer

# Create LLM scorer
llm_scorer = LLMScorer(provider="openai", model="gpt-4o-mini")

# Use in RelevanceScorer
scorer = RelevanceScorer(use_llm=True, llm_scorer=llm_scorer)

# Compute scores (will use LLM for semantic similarity)
score = scorer.compute_score(root_paper, target_paper)
print(f"Relevance: {score.combined}")
print(f"Explanation: {score.llm_explanation}")
```

## Cost Considerations

### API Costs

- **OpenAI GPT-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Anthropic Claude Haiku**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- **HuggingFace**: Free (runs locally, requires GPU)

### Cost Estimation

For a typical run with:
- 20 papers to score
- ~500 tokens per paper pair
- Explanations enabled

**Estimated cost**: $0.01 - $0.05 per run (with GPT-4o-mini)

### Cost Optimization Tips

1. **Use smaller models**: `gpt-4o-mini` or `claude-3-haiku` are cost-effective
2. **Limit depth**: Use `depth=1` instead of `depth=2` to score fewer papers
3. **Limit papers per level**: Use `max_per_level=5` instead of `max_per_level=10`
4. **Disable explanations**: Set `use_explanations=False` for faster/cheaper scoring
5. **Use caching**: LLM scores aren't cached yet, but you can cache paper data

## Output Format

### Console Output

When using LLM scoring, you'll see:

```
TOP 10 MOST RELEVANT PAPERS (LLM-based scoring with explanations)

1. Paper Title Here
   └─ Relevance: 0.6800
      ├─ Semantic (LLM): 0.8500
      ├─ Bib. Coupling: 0.1200
      ├─ Year Similarity: 0.9500
      └─ Citation Score: 0.7000

      💡 Explanation: Both papers focus on antioxidant mechanisms in cellular 
         systems, using similar experimental methodologies. They address 
         complementary aspects of oxidative stress response.
```

### CSV Output

The CSV file includes an `llm_explanation` column with the explanation text.

### Visualization

Hover over nodes in the HTML graph to see LLM explanations in tooltips.

## Comparison: LLM vs SPECTER2

| Feature | SPECTER2 | LLM |
|---------|----------|-----|
| **Speed** | Fast (local) | Slower (API calls) |
| **Cost** | Free | ~$0.01-0.05 per run |
| **Explanations** | No | Yes |
| **Accuracy** | High (trained on citations) | High (contextual understanding) |
| **Customization** | Limited | High (prompt engineering) |

## Troubleshooting

### "ModuleNotFoundError: openai"

```bash
pip install openai
```

### "API key required"

Make sure you've set the environment variable:
```bash
export OPENAI_API_KEY="your-key-here"
```

### "LLM scoring failed"

- Check your API key is valid
- Check your API quota/balance
- Try a different model
- Check internet connection

### Slow performance

- Use smaller models (`gpt-4o-mini` instead of `gpt-4`)
- Reduce `depth` and `max_per_level`
- Disable explanations (`use_explanations=False`)

## Advanced Usage

### Custom Prompts

You can modify the prompt in `relevance_scoring/llm_scorer.py`:

```python
def _create_prompt(self, root_paper, target_paper):
    # Customize this method to change how papers are compared
    ...
```

### Hybrid Scoring

You can use both SPECTER2 and LLM:

```python
# Use SPECTER2 for initial filtering
scorer_embedding = RelevanceScorer(use_llm=False)
edges = scorer_embedding.compute_relevance_edges(root_paper)

# Use LLM only for top papers
llm_scorer = LLMScorer(provider="openai")
scorer_llm = RelevanceScorer(use_llm=True, llm_scorer=llm_scorer)

# Score top 10 with LLM
top_papers = sorted(edges, key=lambda x: x.relevance_score.combined, reverse=True)[:10]
for edge in top_papers:
    llm_score = scorer_llm.compute_score(root_paper, target_paper)
    print(llm_score.llm_explanation)
```

## Examples

See `experiments/visualize_with_llm.py` for a complete working example.

