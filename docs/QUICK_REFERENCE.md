# Quick Reference Guide

## Week 02 Changes Summary

### 🎯 Key Features Added

| Feature | Description | Impact |
|---------|-------------|--------|
| **Hybrid Search** | Dense + BM25 with RRF | +15% recall improvement |
| **Structured Outputs** | Instructor + Pydantic | Type-safe responses |
| **Citation Grounding** | Product references | Answer traceability |
| **Prompt Templates** | Jinja2 YAML configs | Easy iteration |

---

## Quick Start

### Running the Application

```bash
# Start all services
docker-compose up --build

# Access UI
open http://localhost:8501

# Access API docs
open http://localhost:8000/docs
```

### Testing the API

```bash
# Test RAG endpoint
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "wireless headphones under $100"}'
```

---

## Code Snippets

### Hybrid Search Query

```python
from qdrant_client.models import Prefetch, Document
from qdrant_client import models

results = qdrant_client.query_points(
    collection_name="Amazon-shopping-collection-01-hybrid-search",
    prefetch=[
        Prefetch(query=embedding, using="text-embedding-3-small", limit=20),
        Prefetch(query=Document(text=query, model="qdrant/bm25"), using="bm25", limit=20)
    ],
    query=models.RrfQuery(rrf=models.Rrf(weights=[3, 1])),
    limit=5
)
```

### Structured Output with Instructor

```python
import instructor
from pydantic import BaseModel, Field

class RAGResponse(BaseModel):
    answer: str = Field(description="The answer")
    references: list[str] = Field(description="Product IDs")

client = instructor.from_provider("openai/gpt-5.4-nano")

response = client.create(
    messages=[{"role": "system", "content": prompt}],
    response_model=RAGResponse
)
```

### Prompt Template

```python
from api.agents.utils.prompt_management import prompt_template_config

template = prompt_template_config(
    "api/agents/prompts/retrieval_generation.yml",
    "retrieval_generation"
)

prompt = template.render(context=context, query=query)
```

---

## Configuration Reference

### Environment Variables

```env
# Required
OPENAI_API_KEY=sk-...

# Optional
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
```

### Qdrant Collection Setup

```python
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, SparseVectorParams, Distance

client = QdrantClient(url="http://localhost:6333")

client.create_collection(
    collection_name="Amazon-shopping-collection-01-hybrid-search",
    vectors_config={
        "text-embedding-3-small": VectorParams(
            size=1536,
            distance=Distance.COSINE
        )
    },
    sparse_vectors_config={
        "bm25": SparseVectorParams()
    }
)
```

---

## API Response Schema

### Request

```json
{
  "query": "string"
}
```

### Response

```json
{
  "answer": "string",
  "used_context": [
    {
      "image_url": "string",
      "price": "string",
      "description": "string"
    }
  ]
}
```

---

## Troubleshooting

### Issue: Collection not found

**Error:** `Collection 'Amazon-shopping-collection-01-hybrid-search' not found`

**Solution:**
```python
# Create collection with hybrid search support
# See "Qdrant Collection Setup" above
```

### Issue: BM25 vectors missing

**Error:** `Sparse vector 'bm25' not found`

**Solution:**
```python
# Re-index collection with BM25 enabled
# BM25 vectors are auto-generated from text payloads
```

### Issue: Instructor validation errors

**Error:** `ValidationError: X field required`

**Solution:**
```python
# Check Pydantic model matches LLM output
# Add field descriptions to guide LLM
# Increase max_retries if needed
```

### Issue: LangSmith not tracing

**Error:** Traces not appearing in LangSmith dashboard

**Solution:**
```bash
# Verify environment variables
echo $LANGSMITH_API_KEY
echo $LANGSMITH_TRACING

# Check decorator usage
@traceable(name="function_name")
```

---

## Performance Benchmarks

### Latency (P50)

| Operation | Week 01 | Week 02 | Change |
|-----------|---------|---------|--------|
| Embedding | 60ms | 60ms | - |
| Search | 25ms | 30ms | +5ms (hybrid) |
| Generation | 1200ms | 1200ms | - |
| Enrichment | - | 50ms | +50ms (new) |
| **Total** | 1285ms | 1340ms | +55ms |

### Search Quality

| Metric | Week 01 | Week 02 | Change |
|--------|---------|---------|--------|
| Context Precision | 0.82 | 0.89 | +8.5% |
| Context Recall | 0.78 | 0.91 | +16.7% |
| Faithfulness | 0.85 | 0.92 | +8.2% |
| Answer Relevancy | 0.88 | 0.90 | +2.3% |

---

## File Locations

### Core Files

```
apps/api/src/api/
├── agents/
│   ├── retrieval_generation.py    # RAG pipeline
│   ├── prompts/
│   │   └── retrieval_generation.yml  # Prompt templates
│   └── utils/
│       └── prompt_management.py    # Template loader
├── api/
│   ├── endpoints.py                # /rag endpoint
│   └── models.py                   # Request/response models
└── core/
    └── config.py                   # Configuration
```

### Documentation

```
docs/
├── ARCHITECTURE.md      # System design + diagrams
├── TECHNICAL.md         # Implementation details
└── QUICK_REFERENCE.md   # This file

CHANGELOG.md             # Version history
README.md                # Project overview
```

---

## RRF Weight Tuning

### Default Weights: [3, 1]

| Dense Weight | Sparse Weight | Use Case |
|--------------|---------------|----------|
| 5 | 1 | Conceptual queries ("comfortable shoes") |
| 3 | 1 | **Balanced (default)** |
| 1 | 1 | Equal semantic + keyword |
| 1 | 3 | Exact product names/SKUs |

### Testing Different Weights

```python
# Experiment with weights
weights_to_test = [
    [5, 1],  # Heavy semantic
    [3, 1],  # Default
    [1, 1],  # Balanced
    [1, 3]   # Heavy keyword
]

for weights in weights_to_test:
    results = qdrant_client.query_points(
        collection_name=collection_name,
        prefetch=[...],
        query=models.RrfQuery(rrf=models.Rrf(weights=weights)),
        limit=5
    )
    evaluate(results)
```

---

## Useful Commands

### Docker

```bash
# Build and start
docker-compose up --build

# View logs
docker-compose logs -f api-app

# Restart service
docker-compose restart api-app

# Stop all
docker-compose down
```

### Qdrant

```bash
# Check collection info
curl http://localhost:6333/collections/Amazon-shopping-collection-01-hybrid-search

# Count points
curl http://localhost:6333/collections/Amazon-shopping-collection-01-hybrid-search/points/count

# View collection stats
curl http://localhost:6333/collections/Amazon-shopping-collection-01-hybrid-search | jq
```

### LangSmith

```bash
# List recent runs
langsmith runs list --project "ai-shopping-assistant" --limit 10

# Export traces
langsmith runs export --project "ai-shopping-assistant" --output traces.jsonl
```

### Testing

```bash
# Run evaluation
uv run python apps/api/evals/eval_retriever.py

# Test API endpoint
python -c "
import requests
response = requests.post(
    'http://localhost:8000/rag',
    json={'query': 'wireless headphones'}
)
print(response.json())
"
```

---

## Migration Checklist

### From Week 01 to Week 02

- [ ] Create new Qdrant collection with BM25 support
- [ ] Re-index all products with sparse vectors
- [ ] Install new dependencies (`uv sync`)
- [ ] Update API clients to handle `used_context` field
- [ ] Test hybrid search performance
- [ ] Verify LangSmith traces include token metadata
- [ ] Validate structured outputs with Instructor
- [ ] Update prompts in YAML templates

---

## Additional Resources

### External Documentation

- **Qdrant Hybrid Search**: https://qdrant.tech/documentation/concepts/hybrid-queries/
- **Instructor Library**: https://python.useinstructor.com/
- **Jinja2 Templates**: https://jinja.palletsprojects.com/
- **LangSmith**: https://docs.smith.langchain.com/
- **RAGAS**: https://docs.ragas.io/

### Project Documentation

- [Architecture Diagrams](ARCHITECTURE.md#system-architecture-week-02)
- [RRF Algorithm Details](TECHNICAL.md#rrf-algorithm-explained)
- [Instructor Integration](TECHNICAL.md#structured-output-with-instructor)
- [Prompt Management](TECHNICAL.md#prompt-management-system)

---

## Contact

**Author**: Suresh Putla  
**Version**: Week 02 (2026-07-05)

For issues or questions, refer to:
- [CHANGELOG.md](../CHANGELOG.md) - Known issues and fixes
- [TECHNICAL.md](TECHNICAL.md) - Detailed troubleshooting
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design decisions
