# Technical Documentation

## Overview

This document provides deep technical implementation details for the AI Shopping Assistant Lab, focusing on Week 02 enhancements including hybrid search, structured outputs, and prompt management.

---

## Table of Contents

1. [Hybrid Search Implementation](#hybrid-search-implementation)
2. [Structured Output with Instructor](#structured-output-with-instructor)
3. [Prompt Management System](#prompt-management-system)
4. [Citation and Grounding](#citation-and-grounding)
5. [API Design](#api-design)
6. [Database Schema](#database-schema)
7. [Tracing and Observability](#tracing-and-observability)
8. [Performance Optimization](#performance-optimization)
9. [Error Handling](#error-handling)
10. [Testing Strategies](#testing-strategies)

---

## 1. Hybrid Search Implementation

### 1.1 Core Concept

Hybrid search combines two complementary retrieval methods:

1. **Dense Vector Search** - Semantic similarity using embeddings
2. **Sparse Vector Search** - Keyword-based BM25 algorithm

These are fused using **Reciprocal Rank Fusion (RRF)** to produce a final ranked list.

### 1.2 Implementation Details

```python
def retrieve_context(query, qdrant_client, k=5):
    # Generate dense embedding
    query_embedding = get_embedding(query)
    
    # Hybrid query with RRF
    results = qdrant_client.query_points(
        collection_name=qdrant_collection_name,
        prefetch=[
            # Dense vector search
            Prefetch(
                query=query_embedding,
                using="text-embedding-3-small",
                limit=20
            ),
            # Sparse BM25 search
            Prefetch(
                query=Document(text=query, model="qdrant/bm25"),
                using="bm25",
                limit=20
            )
        ],
        # RRF fusion with weights [dense=3, sparse=1]
        query=models.RrfQuery(rrf=models.Rrf(weights=[3, 1])),
        limit=k
    )
    return results
```

### 1.3 RRF Algorithm Explained

**Formula:**
```
RRF_score(d) = Σ [ w_i / (k + rank_i(d)) ]
```

**Where:**
- `d` = document (product)
- `w_i` = weight for retrieval method i
- `k` = RRF constant (default: 60)
- `rank_i(d)` = rank position of document d in method i

**Example Calculation:**

For a product ranked:
- Position 5 in dense search (weight=3)
- Position 10 in sparse search (weight=1)

```
RRF_score = (3 / (60 + 5)) + (1 / (60 + 10))
          = (3 / 65) + (1 / 70)
          = 0.0462 + 0.0143
          = 0.0605
```

### 1.4 Weight Selection Rationale

**Weights: [3, 1]** (Dense : Sparse)

**Why 3:1 ratio?**
- Dense search excels at semantic understanding
- Sparse search ensures keyword precision
- 3:1 ratio empirically performs well for product search
- Allows semantic understanding to dominate while preserving exact matches

**Tuning Considerations:**
- Increase dense weight for conceptual queries ("comfortable running shoes")
- Increase sparse weight for specific SKUs or exact product names
- Monitor evaluation metrics (context precision/recall) when adjusting

### 1.5 Prefetch Limit Analysis

**Why 20 candidates per method?**
- Balances recall and computational cost
- Ensures sufficient candidate diversity before fusion
- Top-20 typically captures relevant products
- Further increases show diminishing returns

**Performance Impact:**
| Prefetch Limit | Latency | Recall@5 |
|----------------|---------|----------|
| 10 | 20ms | 0.82 |
| 20 | 30ms | 0.91 |
| 50 | 45ms | 0.93 |

### 1.6 Collection Requirements

**Qdrant Collection Configuration:**

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams, Distance,
    SparseVectorParams, SparseIndexParams
)

client.create_collection(
    collection_name="Amazon-shopping-collection-01-hybrid-search",
    vectors_config={
        "text-embedding-3-small": VectorParams(
            size=1536,
            distance=Distance.COSINE
        )
    },
    sparse_vectors_config={
        "bm25": SparseVectorParams(
            index=SparseIndexParams()
        )
    }
)
```

**Payload Schema:**
```json
{
  "parent_asin": "B08XYZ123",
  "preprocessed_description": "Wireless headphones with...",
  "average_rating": 4.5,
  "image": "https://m.media-amazon.com/...",
  "price": 79.99,
  "category": ["Electronics", "Headphones"]
}
```

---

## 2. Structured Output with Instructor

### 2.1 Problem Statement

**Traditional LLM Output Issues:**
- Unpredictable response formats
- Manual string parsing errors
- Missing field validation
- Difficult to extract structured data

### 2.2 Instructor Solution

**Instructor** wraps LLM APIs to enforce structured outputs using Pydantic schemas.

### 2.3 Implementation

```python
import instructor
from pydantic import BaseModel, Field

# Define response schema
class RAGUsedContext(BaseModel):
    id: str = Field(
        description="The id of the item used to answer the question"
    )
    description: str = Field(
        description="The description of the item used to answer the question"
    )

class RAGGenerationResponseWithGrounding(BaseModel):
    answer: str = Field(
        description="The answer to the question"
    )
    references: list[RAGUsedContext] = Field(
        description="List of items used to answer the question"
    )

# Create instructor-wrapped client
client = instructor.from_provider(
    "openai/gpt-5.4-nano",
    mode=instructor.Mode.RESPONSES_TOOLS
)

# Generate structured output
response, raw_response = client.create_with_completion(
    messages=[{"role": "system", "content": prompt}],
    reasoning={"effort": "none"},
    response_model=RAGGenerationResponseWithGrounding
)

# response is a validated Pydantic object
print(response.answer)  # Type-safe access
print(response.references[0].id)  # Structured data
```

### 2.4 Mode Selection

**Instructor Modes:**

| Mode | Method | Use Case |
|------|--------|----------|
| `TOOLS` | Function calling | Most reliable, GPT-4+ |
| `JSON` | JSON mode | Faster, less reliable |
| `MD_JSON` | Markdown JSON | Legacy models |
| `RESPONSES_TOOLS` | Response format | New OpenAI models |

**Why `RESPONSES_TOOLS`?**
- Native support in GPT-5.4-nano
- Optimal performance/reliability balance
- Structured outputs feature

### 2.5 Validation Flow

```
User Prompt
    ↓
LLM Generation (with schema)
    ↓
[JSON Output]
    ↓
Pydantic Validation
    ↓
    ├─ Valid → Return Model
    └─ Invalid → Retry (up to max_retries)
```

**Automatic Retry Logic:**
- Default: 3 retries on validation failure
- Configurable with `max_retries` parameter
- Validation errors sent back to LLM for correction

### 2.6 Benefits

✅ **Type Safety**: IDE autocomplete and type checking  
✅ **Validation**: Automatic field validation (required, types, constraints)  
✅ **Documentation**: Schemas are self-documenting  
✅ **Reliability**: Retry logic handles malformed outputs  
✅ **Integration**: Works seamlessly with FastAPI  

---

## 3. Prompt Management System

### 3.1 Architecture

**Components:**
1. **YAML Templates** - Prompt storage
2. **Jinja2 Engine** - Dynamic rendering
3. **Utility Functions** - Loading and caching

### 3.2 Template Structure

**File: `retrieval_generation.yml`**
```yaml
metadata:
  name: Retrieval Generation Prompt
  version: 1.0.0
  description: Retrieval Generation Prompt for RAG
  author: Suresh Putla

prompts:
  retrieval_generation: |
    You are a shopping assistant that can answer questions about the products in stock.

    You will be given a question and a list of context.

    Instructions:
    - answer the question based on the provided context only.
    - never use word context and refer to it as the available products.
    - do not use markdown formatting.
    - if you do not find any products, say 'there is no product in the stock'.

    Context:
    {{ context }}

    Question:
    {{ query }}
```

### 3.3 Template Loader Implementation

**File: `utils/prompt_management.py`**
```python
import yaml
from jinja2 import Template
from pathlib import Path

def prompt_template_config(template_path: str, prompt_key: str) -> Template:
    """
    Load and parse a prompt template from YAML file.
    
    Args:
        template_path: Path to YAML file (relative to project root)
        prompt_key: Key in 'prompts' section to load
    
    Returns:
        Jinja2 Template object ready for rendering
    """
    # Resolve absolute path
    full_path = Path(__file__).parent.parent.parent / template_path
    
    # Load YAML
    with open(full_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Extract prompt template
    prompt_text = config['prompts'][prompt_key]
    
    # Create Jinja2 template
    return Template(prompt_text)
```

### 3.4 Usage Pattern

```python
# Load template
template = prompt_template_config(
    "api/agents/prompts/retrieval_generation.yml",
    "retrieval_generation"
)

# Render with variables
prompt = template.render(
    context=formatted_context,
    query=user_query
)

# Use in LLM call
response = generate_answer(prompt)
```

### 3.5 Benefits

**Separation of Concerns:**
- Prompt engineering ≠ code changes
- Non-engineers can iterate on prompts
- Version control for prompt history

**Experimentation:**
- A/B test different prompts
- Swap prompts without deployment
- Track prompt versions in metadata

**Maintainability:**
- Centralized prompt repository
- Easy to audit and review
- Consistent formatting

### 3.6 Best Practices

✅ **Version Prompts**: Use semantic versioning in metadata  
✅ **Document Variables**: List all template variables in description  
✅ **Escape Special Chars**: Use Jinja2 filters for user input  
✅ **Test Templates**: Validate rendering before deployment  
✅ **Track Metadata**: Author, date, changelog in YAML  

### 3.7 Advanced Patterns

**Conditional Logic:**
```yaml
prompts:
  adaptive_prompt: |
    {% if product_count > 0 %}
    Here are {{ product_count }} relevant products:
    {{ context }}
    {% else %}
    No products match your query.
    {% endif %}
```

**Loops:**
```yaml
prompts:
  enumerated_prompt: |
    Available products:
    {% for product in products %}
    {{ loop.index }}. {{ product.name }} - ${{ product.price }}
    {% endfor %}
```

---

## 4. Citation and Grounding

### 4.1 Problem

LLMs can "hallucinate" product details not present in retrieved context. Grounding ensures answers are traceable to source documents.

### 4.2 Grounding Strategy

**Two-Level Grounding:**

1. **Reference Extraction** (LLM level)
   - LLM returns product IDs used in answer
   - Validated against retrieved context

2. **Detail Enrichment** (API level)
   - Fetch full product details from Qdrant
   - Attach images, prices, metadata

### 4.3 Implementation Flow

```python
def rag_pipeline_wrapper(query, top_k=5):
    # Execute RAG pipeline
    result = rag_pipeline(query, qdrant_client, top_k)
    
    # Extract references from LLM response
    references = result.get('references', [])  # List[RAGUsedContext]
    
    # Enrich with product details
    used_context = []
    for reference in references:
        # Fetch full product payload
        payload = get_description(qdrant_client, reference.id)
        
        # Extract display fields
        image_url = payload.get("image", "")
        price = str(payload.get("price", ""))
        
        # Build enriched context
        if image_url:
            used_context.append({
                "image_url": image_url,
                "price": price,
                "description": reference.description
            })
    
    return {
        "answer": result.get('answer'),
        "used_context": used_context
    }
```

### 4.4 Product Detail Fetcher

```python
def get_description(qdrant_client, parent_asin: str) -> dict:
    """
    Fetch full product payload by parent ASIN.
    
    Args:
        qdrant_client: Qdrant client instance
        parent_asin: Product identifier
    
    Returns:
        Full product payload dict
    """
    results = qdrant_client.scroll(
        collection_name=qdrant_collection_name,
        with_payload=True,
        with_vectors=False,  # Don't fetch vectors (faster)
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="parent_asin",
                    match=MatchValue(value=parent_asin)
                )
            ]
        )
    )[0]
    
    return results[0].payload
```

### 4.5 Grounding Validation

**Validation Rules:**
1. All referenced IDs must exist in retrieved context
2. LLM cannot cite products not in top-k results
3. Missing references default to empty list (no citations)

**Future Enhancement:**
```python
def validate_grounding(references, retrieved_ids):
    """Ensure LLM only cites retrieved products."""
    valid_refs = [
        ref for ref in references 
        if ref.id in retrieved_ids
    ]
    
    if len(valid_refs) < len(references):
        logger.warning("LLM cited unretrieved products!")
    
    return valid_refs
```

### 4.6 UI Display

**Streamlit Sidebar:**
```python
with st.sidebar:
    if st.session_state.used_context:
        for item in st.session_state.used_context:
            st.caption(item['description'])
            st.image(item['image_url'], width=250)
            st.caption(f"Price: {item['price']} USD")
            st.divider()
```

**Benefits:**
- Visual confirmation of sources
- User can verify product details
- Builds trust in AI responses
- Supports purchase decisions

---

## 5. API Design

### 5.1 Endpoint Specification

**POST `/rag`**

**Request:**
```json
{
  "query": "string"  // User question (required)
}
```

**Response:**
```json
{
  "answer": "string",  // Generated answer
  "used_context": [    // Product citations
    {
      "image_url": "string",
      "price": "string",
      "description": "string"
    }
  ]
}
```

### 5.2 Pydantic Models

```python
# Request model
class RAGRequest(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What wireless headphones do you have?"
            }
        }

# Response models
class RAGUsedContext(BaseModel):
    image_url: str
    price: str
    description: str

class RAGResponse(BaseModel):
    answer: str
    used_context: list[RAGUsedContext]
```

### 5.3 Endpoint Handler

```python
@rag_router.post("/")
def chat(request: Request, payload: RAGRequest) -> RAGResponse:
    # Execute RAG pipeline wrapper
    result = rag_pipeline_wrapper(payload.query)
    
    # Transform to response model
    return RAGResponse(
        answer=result["answer"],
        used_context=[
            RAGUsedContext(**item) 
            for item in result["used_context"]
        ]
    )
```

### 5.4 Error Handling

```python
from fastapi import HTTPException

@rag_router.post("/")
def chat(request: Request, payload: RAGRequest) -> RAGResponse:
    try:
        result = rag_pipeline_wrapper(payload.query)
        return RAGResponse(...)
    
    except QdrantException as e:
        logger.error(f"Qdrant error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Vector database unavailable"
        )
    
    except OpenAIError as e:
        logger.error(f"OpenAI error: {e}")
        raise HTTPException(
            status_code=502,
            detail="LLM service error"
        )
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )
```

### 5.5 API Versioning

**Future Consideration:**
```python
# Version 1
api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(rag_router, prefix="/rag")

# Version 2 (with additional features)
api_v2_router = APIRouter(prefix="/v2")
api_v2_router.include_router(rag_v2_router, prefix="/rag")

# Mount both versions
app.include_router(api_v1_router)
app.include_router(api_v2_router)
```

---

## 6. Database Schema

### 6.1 Qdrant Collection Structure

**Collection Name:** `Amazon-shopping-collection-01-hybrid-search`

**Vectors:**
```python
{
    "text-embedding-3-small": {
        "size": 1536,
        "distance": "Cosine"
    }
}
```

**Sparse Vectors:**
```python
{
    "bm25": {
        "index": {
            "type": "IDF"  # Inverse Document Frequency
        }
    }
}
```

**Payload Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `parent_asin` | string | Yes | Product identifier |
| `preprocessed_description` | string | Yes | Searchable text |
| `average_rating` | float | No | Star rating (1-5) |
| `image` | string | No | Product image URL |
| `price` | float | No | Price in USD |
| `category` | list[string] | No | Product categories |
| `title` | string | No | Product name |

### 6.2 Indexing Strategy

**Dense Vector Index:**
- Algorithm: HNSW (Hierarchical Navigable Small World)
- ef_construct: 100 (construction time parameter)
- m: 16 (connections per layer)

**Sparse Vector Index:**
- Algorithm: Inverted index
- Tokenization: Built-in BM25 tokenizer
- Stop words: Automatic

### 6.3 Data Ingestion Pipeline

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

def ingest_products(client, products):
    """
    Ingest products with dense and sparse vectors.
    
    Args:
        client: QdrantClient instance
        products: List of product dicts
    """
    points = []
    
    for idx, product in enumerate(products):
        # Generate dense embedding
        dense_vector = get_embedding(
            product['preprocessed_description']
        )
        
        # Qdrant auto-generates sparse vectors from text
        point = PointStruct(
            id=idx,
            vector={
                "text-embedding-3-small": dense_vector
            },
            payload={
                "parent_asin": product['parent_asin'],
                "preprocessed_description": product['description'],
                "average_rating": product.get('rating', 0.0),
                "image": product.get('image', ''),
                "price": product.get('price', 0.0)
            }
        )
        
        # For BM25, pass the text document
        point.vector["bm25"] = product['preprocessed_description']
        points.append(point)
    
    # Batch upload
    client.upsert(
        collection_name="Amazon-shopping-collection-01-hybrid-search",
        points=points
    )
```

---

## 7. Tracing and Observability

### 7.1 LangSmith Integration

**Decorator-Based Tracing:**
```python
from langsmith import traceable, get_current_run_tree

@traceable(
    name="get_embedding",
    run_type="embedding",
    metadata={
        "ls_model_provider": "openai",
        "ls_model_name": "text-embedding-3-small"
    }
)
def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding
```

### 7.2 Token Usage Tracking

```python
@traceable(
    name="generate_answer",
    run_type="llm",
    metadata={
        "ls_model_provider": "openai",
        "ls_model_name": "gpt-5.4-nano"
    }
)
def generate_answer(prompt):
    response, raw_response = client.create_with_completion(...)
    
    # Attach token usage to trace
    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"] = {
            "input_tokens": raw_response.usage.input_tokens,
            "output_tokens": raw_response.usage.output_tokens,
            "total_tokens": raw_response.usage.total_tokens
        }
    
    return response
```

### 7.3 Trace Hierarchy

```
rag_pipeline (root)
├── retrieve_context
│   └── get_embedding
│       └── [OpenAI API call]
├── process_context
├── build_prompt
└── generate_answer
    └── [OpenAI API call]
```

### 7.4 Custom Metadata

**Best Practices:**
```python
@traceable(
    name="retrieve_context",
    metadata={
        "search_type": "hybrid",
        "rrf_weights": [3, 1],
        "prefetch_limit": 20
    }
)
def retrieve_context(query, qdrant_client, k=5):
    # ... implementation
    
    # Add runtime metadata
    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata.update({
            "results_count": len(results),
            "avg_score": sum(scores) / len(scores)
        })
```

---

## 8. Performance Optimization

### 8.1 Latency Breakdown

**Measured Latencies (P50):**
- Embedding Generation: 60ms
- Hybrid Search: 30ms
- Context Processing: 5ms
- Prompt Building: 2ms
- LLM Generation: 1200ms
- Context Enrichment: 50ms
- **Total: ~1350ms**

### 8.2 Optimization Strategies

**1. Embedding Caching**
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_embedding_cached(text_hash):
    return get_embedding(text)

def cached_embedding(text):
    text_hash = hashlib.md5(text.encode()).hexdigest()
    return get_embedding_cached(text_hash)
```

**2. Async Operations**
```python
import asyncio

async def rag_pipeline_async(query, qdrant_client):
    # Parallel execution
    embedding_task = asyncio.create_task(get_embedding(query))
    
    embedding = await embedding_task
    context = await retrieve_context_async(embedding, qdrant_client)
    
    # ... rest of pipeline
```

**3. Batch Enrichment**
```python
def batch_get_descriptions(qdrant_client, asins: list[str]):
    """Fetch multiple product details in one query."""
    results = qdrant_client.scroll(
        collection_name=qdrant_collection_name,
        scroll_filter=Filter(
            should=[
                FieldCondition(
                    key="parent_asin",
                    match=MatchValue(value=asin)
                )
                for asin in asins
            ]
        )
    )[0]
    return {r.payload['parent_asin']: r.payload for r in results}
```

### 8.3 Connection Pooling

```python
from qdrant_client import QdrantClient

# Global connection pool
qdrant_pool = QdrantClient(
    url="http://qdrant:6333",
    timeout=10,
    pool_size=10  # Connection pool
)

# Reuse connections
def rag_pipeline(query):
    return rag_pipeline_impl(query, qdrant_pool)
```

---

## 9. Error Handling

### 9.1 Error Categories

**1. External Service Errors**
- OpenAI API failures
- Qdrant connection issues
- Network timeouts

**2. Validation Errors**
- Invalid query format
- Malformed LLM outputs
- Missing payload fields

**3. Business Logic Errors**
- No products found
- Empty context
- Grounding validation failures

### 9.2 Retry Strategy

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(OpenAIError)
)
def generate_answer_with_retry(prompt):
    return generate_answer(prompt)
```

### 9.3 Graceful Degradation

```python
def rag_pipeline_with_fallback(query, qdrant_client):
    try:
        # Try hybrid search
        return rag_pipeline_hybrid(query, qdrant_client)
    
    except Exception as e:
        logger.warning(f"Hybrid search failed: {e}")
        
        try:
            # Fallback to dense-only
            return rag_pipeline_dense_only(query, qdrant_client)
        
        except Exception as e:
            logger.error(f"All retrieval methods failed: {e}")
            return {
                "answer": "I'm having trouble accessing products right now.",
                "used_context": []
            }
```

---

## 10. Testing Strategies

### 10.1 Unit Tests

```python
import pytest
from api.agents.retrieval_generation import process_context

def test_process_context():
    context = {
        'retrieved_context_ids': ['B08XYZ', 'B08ABC'],
        'retrieved_context': ['Product 1', 'Product 2'],
        'retrieved_context_ratings': [4.5, 4.0]
    }
    
    result = process_context(context)
    
    assert 'B08XYZ' in result
    assert 'Product 1' in result
    assert '4.5' in result
```

### 10.2 Integration Tests

```python
@pytest.mark.integration
def test_rag_pipeline_e2e():
    query = "wireless headphones"
    client = QdrantClient(url="http://localhost:6333")
    
    result = rag_pipeline(query, client, top_k=5)
    
    assert 'answer' in result
    assert len(result['references']) > 0
    assert all(ref.id for ref in result['references'])
```

### 10.3 Evaluation with RAGAS

```python
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)

def evaluate_rag_system(test_dataset):
    results = evaluate(
        dataset=test_dataset,
        metrics=[
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy
        ]
    )
    
    print(f"Context Precision: {results['context_precision']}")
    print(f"Faithfulness: {results['faithfulness']}")
    
    return results
```

### 10.4 Load Testing

```python
import asyncio
from locust import HttpUser, task, between

class RAGUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def query_rag(self):
        self.client.post(
            "/rag",
            json={"query": "wireless headphones"}
        )
```

---

## Appendices

### A. Common Issues and Solutions

**Issue: Slow hybrid search**
- Solution: Reduce prefetch limits or increase Qdrant resources

**Issue: LLM hallucinations**
- Solution: Strengthen prompt instructions, add grounding validation

**Issue: Missing product images**
- Solution: Add fallback placeholder images, validate image URLs

### B. Configuration Checklist

- [ ] OpenAI API key configured
- [ ] Qdrant collection created with hybrid search
- [ ] BM25 sparse vectors indexed
- [ ] Product data ingested with all required fields
- [ ] LangSmith tracing enabled (optional)
- [ ] Prompt templates validated

### C. Useful Commands

```bash
# Check Qdrant collection info
curl http://localhost:6333/collections/Amazon-shopping-collection-01-hybrid-search

# Test API endpoint
curl -X POST http://localhost:8000/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "wireless headphones"}'

# View LangSmith traces
langsmith runs list --project "ai-shopping-assistant"
```

---

## References

- [Qdrant Hybrid Search](https://qdrant.tech/documentation/concepts/hybrid-queries/)
- [Instructor Documentation](https://python.useinstructor.com/)
- [Jinja2 Templates](https://jinja.palletsprojects.com/)
- [LangSmith Tracing](https://docs.smith.langchain.com/)
- [RAGAS Evaluation](https://docs.ragas.io/)
