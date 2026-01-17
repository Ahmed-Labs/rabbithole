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

### 3. Spin up Redis, Neo4j, Flask backend, and Celery worker
Make sure you have docker running and run the following command:
```bash
docker compose up -d
```

This will start:
- Redis (message broker and cache)
- Neo4j (graph database)
- Flask API (backend server on port 5000)
- Celery worker (background task processor)

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

### Testing the API

Test a POST request to the relevance endpoint (Windows PowerShell):
```powershell
Invoke-RestMethod `
  -Uri http://localhost:5000/api/get-relevance `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"query":"phasor","max_depth":1,"max_references":10}'
```

You should receive a response with:
```json
{
  "status": "queued",
  "task_id": "abc123..."
}
```

### Monitoring Celery tasks with Flower

To monitor Celery workers and tasks in real-time, run Flower locally:
```bash
celery -A app.celery_app:celery_app flower --port=5555
```

Then access the Flower dashboard at: http://localhost:5555

You can view:
- Active/completed/failed tasks
- Worker status and performance
- Task execution history
- Real-time task monitoring