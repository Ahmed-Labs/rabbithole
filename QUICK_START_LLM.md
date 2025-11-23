# Quick Start: Using LLM-Based Relevance Scoring

## Step 1: Choose Your LLM Provider

You have three options:

### Option A: OpenAI (Recommended - Easiest & Cost-Effective)
- **Models**: GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Cost**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Best for**: Most users, good balance of cost and quality

### Option B: Anthropic Claude
- **Models**: Claude 3 Haiku, Claude 3 Opus
- **Cost**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens
- **Best for**: Users who prefer Claude's style

### Option C: HuggingFace (Local - No API Key Needed)
- **Models**: Any HuggingFace model (requires GPU)
- **Cost**: Free (runs on your machine)
- **Best for**: Users with GPU, want privacy, no API costs

---

## Step 2: Get Your API Key

### For OpenAI (Recommended)

1. **Go to**: https://platform.openai.com/
2. **Sign up** or **Log in** to your account
3. **Navigate to**: API Keys section (https://platform.openai.com/api-keys)
4. **Click**: "Create new secret key"
5. **Copy the key** (you'll only see it once!)
   - It looks like: `sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Important**: 
- You need to add payment method to use the API
- Free tier gives you $5 credit to start
- Set usage limits to avoid unexpected charges

### For Anthropic Claude

1. **Go to**: https://console.anthropic.com/
2. **Sign up** or **Log in**
3. **Navigate to**: API Keys section
4. **Click**: "Create Key"
5. **Copy the key**
   - It looks like: `sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

**Important**:
- Requires adding payment method
- Check pricing at: https://www.anthropic.com/pricing

### For HuggingFace (No API Key Needed)

1. **Go to**: https://huggingface.co/
2. **Sign up** for a free account
3. **No API key needed** - models run locally
4. **Note**: Requires GPU for good performance

---

## Step 3: Install Required Packages

### For OpenAI:
```bash
pip install openai
```

### For Anthropic:
```bash
pip install anthropic
```

### For HuggingFace:
Already installed if you have `transformers` (which is in requirements.txt)

---

## Step 4: Set Your API Key

### Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-proj-your-key-here"
```

### Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-proj-your-key-here
```

### Windows (Permanent - Environment Variables):
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "User variables", click "New"
4. Variable name: `OPENAI_API_KEY`
5. Variable value: `sk-proj-your-key-here`
6. Click OK

### Mac/Linux:
```bash
export OPENAI_API_KEY="sk-proj-your-key-here"
```

### Make it Permanent (Mac/Linux):
Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="sk-proj-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## Step 5: Use the LLM Scorer

### Method 1: Use the Dedicated Script (Easiest)

```bash
# Edit the script first to set your query
python experiments/visualize_with_llm.py
```

**Before running**, edit `experiments/visualize_with_llm.py`:
- Change `query = "antioxidants"` to your search term
- Optionally change `llm_provider = "openai"` 
- Optionally change `llm_model = "gpt-4o-mini"`

### Method 2: Use in Your Own Script

```python
from paper_retrieval.paper_metadata import search, build_full_graph
from relevance_scoring import LLMScorer, compute_relevance_scores

# 1. Search for papers
papers = search("your search query here", limit=10)

# 2. Select root paper
root_paper = papers[0]
print(f"Root paper: {root_paper.title}")

# 3. Build citation graph (start small for LLM to save costs)
root_paper = build_full_graph(
    root_paper,
    depth=1,              # Start with 1 level (fewer papers = lower cost)
    max_per_level=5,       # Limit papers per level
    include_citations=True
)

# 4. Initialize LLM scorer
llm_scorer = LLMScorer(
    provider="openai",           # or "anthropic"
    model="gpt-4o-mini",         # Cost-effective default
    use_explanations=True        # Set False to save costs
)

# 5. Compute relevance scores
print("\nComputing relevance scores with LLM...")
results, scorer = compute_relevance_scores(
    root_paper,
    use_llm=True,
    llm_scorer=llm_scorer
)

# 6. View results
print(f"\nFound {len(results)} papers")
for i, result in enumerate(results[:5], 1):
    print(f"\n{i}. {result['title'][:60]}...")
    print(f"   Relevance: {result['relevance_score']:.3f}")
    if result.get('llm_explanation'):
        print(f"   Explanation: {result['llm_explanation'][:100]}...")
```

### Method 3: Modify Existing Script

Edit `experiments/visualize_relevance_scores.py`:

```python
# Around line 227, change:
use_llm = True  # Change from False to True

# Add LLM scorer initialization:
from relevance_scoring import LLMScorer
llm_scorer = LLMScorer(
    provider="openai",
    model="gpt-4o-mini",
    use_explanations=True
)
```

Then update the `compute_relevance_scores` call:
```python
results, scorer = compute_relevance_scores(
    root_paper,
    use_llm=True,          # Add this
    llm_scorer=llm_scorer, # Add this
    max_depth=depth,
    use_cache=True
)
```

---

## Step 6: Run It!

```bash
# Make sure API key is set
echo $OPENAI_API_KEY  # Should show your key (or use: $env:OPENAI_API_KEY on Windows)

# Run the script
python experiments/visualize_with_llm.py
```

---

## Example: Complete Workflow

```python
# 1. Set API key (or use environment variable)
import os
os.environ['OPENAI_API_KEY'] = 'sk-proj-your-key-here'

# 2. Import
from paper_retrieval.paper_metadata import search, build_full_graph
from relevance_scoring import LLMScorer, compute_relevance_scores

# 3. Search
papers = search("machine learning transformers", limit=5)
root_paper = papers[0]

# 4. Build graph (small for testing)
root_paper = build_full_graph(root_paper, depth=1, max_per_level=3)

# 5. Score with LLM
llm_scorer = LLMScorer(provider="openai", model="gpt-4o-mini")
results, _ = compute_relevance_scores(root_paper, use_llm=True, llm_scorer=llm_scorer)

# 6. View top results
for r in results[:3]:
    print(f"{r['title'][:50]}")
    print(f"  Score: {r['relevance_score']:.2f}")
    print(f"  Explanation: {r.get('llm_explanation', 'N/A')[:80]}...")
    print()
```

---

## Cost Estimation

For a typical run:
- **20 papers** to score
- **~500 tokens** per paper pair
- **GPT-4o-mini** with explanations

**Estimated cost**: $0.01 - $0.05 per run

**To reduce costs**:
- Use `gpt-4o-mini` instead of `gpt-4`
- Set `depth=1` instead of `depth=2`
- Set `max_per_level=5` instead of `max_per_level=10`
- Set `use_explanations=False` (scores only, no explanations)

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "API key required"
- Check environment variable is set: `echo $OPENAI_API_KEY`
- Or pass directly: `llm_scorer = LLMScorer(provider="openai", api_key="sk-proj-...")`

### "Insufficient quota" or "Rate limit exceeded"
- Check your OpenAI account has credits
- Wait a few minutes and try again
- Reduce `max_per_level` to score fewer papers

### "LLM scoring failed"
- Check internet connection
- Verify API key is correct
- Check API service status (https://status.openai.com/)

### Slow performance
- Normal! LLM API calls take time
- Each paper comparison takes 2-5 seconds
- Consider using `use_explanations=False` for faster scoring

---

## Next Steps

1. **Try it**: Run `python experiments/visualize_with_llm.py`
2. **Check output**: Look at `output/references_graph_llm.html`
3. **Review CSV**: Check `output/relevance_scores_llm.csv` for explanations
4. **Customize**: Adjust prompts, models, or parameters as needed

---

## Quick Reference

```python
# Minimal example
from relevance_scoring import LLMScorer, compute_relevance_scores
from paper_retrieval.paper_metadata import search, build_full_graph

papers = search("your query")
root = build_full_graph(papers[0], depth=1, max_per_level=5)

llm = LLMScorer(provider="openai", model="gpt-4o-mini")
results, _ = compute_relevance_scores(root, use_llm=True, llm_scorer=llm)

print(results[0]['llm_explanation'])  # See explanation!
```

That's it! You're ready to use LLM-based relevance scoring. 🚀

