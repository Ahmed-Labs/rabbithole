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

### 3. Spin up Redis and Neo4j
Make sure you have docker running and run the following command:
```bash
docker compose up -d
```

### 4. Run any module/submodule. Example:
```bash
python -m experiments.visualize_relevance_scores
```

### Development Tips

### Neo4j

Access the neo4j interactive UI through: http://localhost:7474/

After logging in, you can run Cypher queries like `MATCH p=()-[r:RELEVANT_TO]->() RETURN p`

### Code formatting

Upon making changes, run the following tools to format and order imports:
```bash
isort .
black .
```

### Celery setup (tentative, will move to docker)

1. get backend running with
```bash
python run.py
```

2. get redis container running with
```bash
docker run -p 6379:6379 redis
```

3. get celery worker running with
```bash
celery -A app.celery_app:celery_app worker --pool=solo --loglevel=INFO -E
```

4. optional - get flower monitoring tool for celery with
```bash
celery -A app.celery_app:celery_app flower --port=5555
```

