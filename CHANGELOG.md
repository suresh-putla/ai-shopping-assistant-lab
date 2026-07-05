# Changelog

All notable changes to the AI Shopping Assistant Lab project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to semantic versioning.

---

## [Week 02] - 2026-07-05

### Added

#### Hybrid Search Implementation
- **Weighted Reciprocal Rank Fusion (RRF)** combining dense and sparse retrieval
  - Dense vector search using `text-embedding-3-small` (OpenAI)
  - Sparse keyword search using `qdrant/bm25` 
  - RRF fusion weights: `[3, 1]` (3x weight for dense, 1x for sparse)
  - Prefetch limit: 20 candidates per method before fusion
  - Final result: Top 5 products after RRF ranking

#### Structured Outputs with Instructor
- **Instructor library integration** for type-safe LLM responses
- **Pydantic models** for structured output validation:
  - `RAGUsedContext`: Product ID and description
  - `RAGGenerationResponseWithGrounding`: Answer with list of references
- **Automatic JSON schema** generation from Pydantic models
- **Type safety** and validation for LLM responses

#### Citation and Grounding System
- **Product references** extracted from LLM responses
- **Automatic product detail enrichment** with images and prices
- **Traceability** - every answer linked to specific product IDs
- **Visual product cards** in Streamlit sidebar showing:
  - Product images
  - Prices (USD)
  - Descriptions
  - Source product IDs

#### Prompt Management System
- **Jinja2 template-based prompts** for maintainability
- **YAML configuration** for prompt storage (`retrieval_generation.yml`)
- **Metadata tracking** for prompts (name, version, author, description)
- **Dynamic rendering** with context and query variables
- **Centralized prompt management** via `prompt_template_config` utility

### Changed

#### Collection and Infrastructure
- **Collection name**: `Amazon-shopping-collection-01` → `Amazon-shopping-collection-01-hybrid-search`
- **Requires BM25 sparse vectors** in Qdrant collection (breaking change)
- **Collection schema** must include both dense and sparse vector indices

#### API Response Format
- **Previous format**:
  ```json
  {
    "answer": "string"
  }
  ```
- **New format**:
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

#### RAG Pipeline Flow
- **Retrieval**: Single dense vector search → Hybrid search with RRF fusion
- **Generation**: Direct OpenAI API call → Instructor-wrapped structured generation
- **Context enrichment**: Added `get_description()` function to fetch product details
- **Response format**: Plain text → Structured with references

#### UI Enhancements
- **Sidebar layout** with dedicated "Suggestions" tab
- **Product card display** with images, prices, and descriptions
- **Session state management** for used context tracking
- **Rerun mechanism** to update sidebar after each query

### Dependencies

#### New Dependencies Added
- `instructor` - Structured outputs from LLMs
- `jinja2` - Template rendering for prompts
- Additional Qdrant models: `Document`, `Prefetch`, `FusionQuery`, `Rrf`

#### Updated in `pyproject.toml`
```toml
[project.dependencies]
instructor = "^1.0.0"
jinja2 = "^3.1.0"
```

### Technical Improvements

#### LangSmith Tracing
- **Enhanced metadata tracking** for token usage
- **Updated field names**: 
  - `prompt_tokens` → `input_tokens`
  - `completion_tokens` → `output_tokens`
- **Preserved total_tokens** tracking

#### Code Organization
- **New utility module**: `api.agents.utils.prompt_management`
- **Wrapper function**: `rag_pipeline_wrapper()` for endpoint integration
- **Separation of concerns**: Core RAG logic vs. API response formatting

---

## [Week 01] - 2026-06-28

### Added
- Initial RAG-based shopping assistant implementation
- FastAPI backend service
- Streamlit chat UI
- Qdrant vector database integration
- OpenAI embeddings with `text-embedding-3-small`
- OpenAI LLM generation with `gpt-5.4-nano`
- LangSmith tracing integration
- RAGAS evaluation pipeline
- Docker Compose orchestration
- Basic prompt engineering for shopping assistant

### Features
- Query embedding generation
- Top-5 vector similarity search
- Context-aware answer generation
- Chat interface with message history
- Environment-based configuration
- Evaluation metrics (Context Precision, Context Recall, Faithfulness, Response Relevancy)

---

## Migration Notes

### Week 01 → Week 02

#### Required Actions

1. **Update Qdrant Collection**:
   - Create new collection with BM25 sparse vectors enabled
   - Re-index all products with both dense and sparse embeddings
   - Collection name: `Amazon-shopping-collection-01-hybrid-search`

2. **Install New Dependencies**:
   ```bash
   uv sync
   ```

3. **Update Environment Variables** (no changes required, but verify):
   - `OPENAI_API_KEY`
   - `LANGSMITH_API_KEY` (optional)

4. **Update Client Code** (if consuming the API):
   - Parse new `used_context` array in responses
   - Handle product images and prices in UI

#### Breaking Changes

- ⚠️ **Collection name changed** - old collection will not work
- ⚠️ **API response schema changed** - clients must handle `used_context`
- ⚠️ **Qdrant collection must support BM25** - requires re-indexing

#### Backward Compatibility

- The core `/rag` endpoint path remains unchanged
- Request format (`{"query": "string"}`) remains unchanged
- The `answer` field in responses is preserved

---

## Roadmap

### Upcoming Features (Week 03+)
- [ ] Semantic caching for faster repeated queries
- [ ] Multi-modal search (image + text)
- [ ] Personalized recommendations
- [ ] Query classification and routing
- [ ] A/B testing framework for RAG parameters
- [ ] Advanced filtering (price range, ratings, categories)
- [ ] Conversational memory across sessions

---

## Contributors

- Suresh Putla - Initial implementation and Week 02 enhancements
