# How to Run the Paper Comparison Program

## Quick Start (3 Steps)

### Step 1: Set Your API Key

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-actual-key-here"
```

**Windows Command Prompt:**
```cmd
set OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 2: Navigate to Project Directory

```bash
cd C:\Users\Alan1\OneDrive\Documents\Capstone_2025\rabbithole
```

### Step 3: Run the Program

```bash
python compare_two_papers.py
```

That's it! The program will guide you through the rest.

---

## Detailed Instructions

### Prerequisites

1. **Python installed** (3.8 or higher)
2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   pip install openai  # For LLM scoring
   ```
3. **API key set** (see Step 1 above)

### Running the Interactive Script

1. **Open terminal/command prompt** in the project directory

2. **Set API key** (if not already set permanently):
   ```powershell
   $env:OPENAI_API_KEY="your-key-here"
   ```

3. **Run the script**:
   ```bash
   python compare_two_papers.py
   ```

4. **Follow the prompts**:
   - Choose how to get Paper 1 (search, by ID, or manual)
   - Choose how to get Paper 2 (search, by ID, or manual)
   - Choose whether to use LLM (if API key is set)
   - View the comparison results!

### Example Session

```
PAPER COMPARISON TOOL
================================================================================

This tool lets you compare two research papers.
You can search for papers or enter them manually.

PAPER 1:
1. Search for paper
2. Enter by Semantic Scholar ID
3. Enter manually
Choose option (1, 2, or 3): 1

Enter search query: machine learning transformers

Searching for: machine learning transformers...

Found 10 papers:
1. Attention Is All You Need
   Vaswani et al. (2017)
2. BERT: Pre-training of Deep Bidirectional Transformers...
   Devlin et al. (2018)
...

Select paper (1-10) or 'q' to cancel: 1

PAPER 2:
1. Search for paper
2. Enter by Semantic Scholar ID
3. Enter manually
Choose option (1, 2, or 3): 1

Enter search query: neural networks

[Similar process...]

Use LLM for comparison? (y/n, default=y): y

================================================================================
COMPARING PAPERS
================================================================================

📄 Paper 1:
   Title: Attention Is All You Need
   Authors: Vaswani et al.
   Year: 2017
   Abstract: The dominant sequence transduction models are based on complex...

📄 Paper 2:
   Title: Deep Residual Learning for Image Recognition
   Authors: He et al.
   Year: 2015
   Abstract: We present a residual learning framework to ease the training...

================================================================================
COMPUTING SIMILARITY...
================================================================================

Using LLM (openai) for comparison...
(This may take 10-20 seconds)

================================================================================
RESULTS
================================================================================

🎯 Similarity Score: 0.65 (on 0.0-1.0 scale)
   Equivalent to: 6.5/10

💡 Explanation:
   Both papers are in the deep learning domain and use neural networks,
   but they address different problems: transformers for sequence modeling
   vs. residual networks for image recognition. They share foundational
   concepts but differ in architecture and application domain.
```

---

## Alternative: Simple Code Example

If you prefer to write your own script:

```bash
python simple_compare_example.py
```

Or create your own:

```python
from paper_retrieval.paper_metadata import search
from relevance_scoring import LLMScorer

# Search for papers
papers1 = search("your query 1")
papers2 = search("your query 2")

# Compare
llm_scorer = LLMScorer(provider="openai", model="gpt-4o-mini")
result = llm_scorer.compute_score(papers1[0], papers2[0])

print(f"Score: {result['relevance_score']:.2f}")
print(f"Explanation: {result['explanation']}")
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai'"
```bash
pip install openai
```

### "API key required"
- Make sure you set the environment variable
- Check: `$env:OPENAI_API_KEY` (PowerShell) or `echo %OPENAI_API_KEY%` (CMD)
- Restart terminal after setting permanently

### "No papers found"
- Try a different search query
- Check your internet connection
- Semantic Scholar API might be temporarily unavailable

### "LLM scoring failed"
- Check your API key is correct
- Check you have credits/balance in OpenAI account
- Check internet connection
- The script will fall back to SPECTER2 embeddings automatically

### Script won't run
- Make sure you're in the project directory
- Check Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`

---

## What Happens When You Run It?

1. **Script starts** and shows menu
2. **You select Paper 1** (search, ID, or manual)
3. **You select Paper 2** (search, ID, or manual)
4. **Script fetches paper information** from Semantic Scholar
5. **Script calls LLM** (or SPECTER2) to compare papers
6. **Results displayed** with score and explanation
7. **Option to compare another pair**

---

## Quick Reference

```bash
# 1. Set API key
$env:OPENAI_API_KEY="your-key"

# 2. Run program
python compare_two_papers.py

# 3. Follow prompts
```

That's all you need! 🚀

