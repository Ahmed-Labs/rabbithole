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