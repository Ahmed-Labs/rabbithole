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
- Neo4j (graph database) - http://localhost:7474
- Flask API (backend server) - http://localhost:5000
- Celery worker (background task processor)
- Flower (Celery monitoring) - http://localhost:5555

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

**1. Submit a task** (Windows PowerShell):
```powershell
$response = Invoke-RestMethod `
  -Uri http://localhost:5000/api/get-relevance `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"query":"phasor","max_depth":1,"max_references":10}'

$taskId = $response.task_id
```

**2. Check task status:**
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/task-status/$taskId"
```

Response when complete:
```json
{
  "task_id": "abc123...",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "query": "phasor",
    "root_paper": "...",
    "papers_processed": 42
  }
}
```

**3. Verify in Neo4j:**
Navigate to http://localhost:7474 and run queries to view the persisted knowledge graph.

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