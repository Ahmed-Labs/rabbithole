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

### Celery setup, assuming redis is up (tentative, will move following steps to docker)

1. get backend running with
```bash
flask run
```

2. get celery worker running with
```bash
celery -A app.celery_app:celery_app worker --pool=solo --loglevel=INFO -E
```

3. optional - get flower monitoring tool for celery with
```bash
celery -A app.celery_app:celery_app flower --port=5555
```

4. test a post request on windows
> Invoke-RestMethod ` 
>>   -Uri http://localhost:5000/api/get-relevance `
>>   -Method POST `
>>   -Headers @{ "Content-Type" = "application/json" } `
>>   -Body '{"query":"chinese ev","max_depth":1,"max_references":10}'