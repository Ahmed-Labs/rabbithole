# Where to Put Your OpenAI API Key

## ⚠️ IMPORTANT: Never put API keys in code files!

API keys should **never** be committed to Git or shared publicly.

---

## ✅ Recommended: Environment Variable

Set your API key as an **environment variable**. This is the safest method.

### Windows PowerShell:
```powershell
$env:OPENAI_API_KEY="sk-proj-your-actual-key-here"
```

### Windows Command Prompt:
```cmd
set OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Windows (Permanent - System Settings):
1. Press `Win + R`
2. Type `sysdm.cpl` and press Enter
3. Click **"Environment Variables"**
4. Under **"User variables"**, click **"New"**
5. Variable name: `OPENAI_API_KEY`
6. Variable value: `sk-proj-your-actual-key-here`
7. Click **OK**

**Note**: If you set it permanently, you may need to restart your terminal/IDE.

### Mac/Linux:
```bash
export OPENAI_API_KEY="sk-proj-your-actual-key-here"
```

### Make it Permanent (Mac/Linux):
Add to `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export OPENAI_API_KEY="sk-proj-your-actual-key-here"' >> ~/.bashrc
source ~/.bashrc
```

---

## ✅ Alternative: .env File (For Local Development)

You can use a `.env` file if you prefer, but **make sure it's in .gitignore**!

### Step 1: Create `.env` file in project root:
```bash
# .env (in project root)
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 2: Install python-dotenv:
```bash
pip install python-dotenv
```

### Step 3: Load in your code:
```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env file

# Now you can use it
from relevance_scoring import LLMScorer
llm = LLMScorer(provider="openai")  # Uses OPENAI_API_KEY from .env
```

### Step 4: Make sure .env is in .gitignore:
The `.gitignore` file should include:
```
.env
```

---

## ❌ DON'T Do This:

**Never hardcode in Python files:**
```python
# ❌ BAD - Don't do this!
api_key = "sk-proj-your-actual-key-here"
```

**Never commit .env files:**
```bash
# ❌ BAD - Don't commit .env!
git add .env
```

---

## How to Verify It's Set:

### Check in PowerShell:
```powershell
$env:OPENAI_API_KEY
```

### Check in Command Prompt:
```cmd
echo %OPENAI_API_KEY%
```

### Check in Mac/Linux:
```bash
echo $OPENAI_API_KEY
```

### Test in Python:
```python
import os
key = os.getenv("OPENAI_API_KEY")
if key:
    print(f"✓ API key is set (starts with: {key[:10]}...)")
else:
    print("✗ API key not found")
```

---

## Quick Start:

1. **Get your API key** from: https://platform.openai.com/api-keys
2. **Set environment variable** (see methods above)
3. **Verify it's set**: `echo $OPENAI_API_KEY` (or `$env:OPENAI_API_KEY` on Windows)
4. **Run your script**: `python compare_two_papers.py`

The code will automatically use the environment variable - no need to modify any files!

---

## Which Method Should I Use?

- **Environment Variable**: Best for most users, works everywhere
- **.env File**: Good if you want to keep keys in a file (but still secure with .gitignore)

Both methods keep your key out of your code, which is the important part!

