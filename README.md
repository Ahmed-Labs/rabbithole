### Setup Instructions

### 1. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Spin up redis container
Make sure you have docker running and run the following command:
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 4. Run any module/submodule. Example:
```bash
python -m experiments.visualize_relevance_scores
```