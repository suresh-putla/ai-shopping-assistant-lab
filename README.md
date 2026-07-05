# AI Shopping Assistant Lab

A production-grade RAG (Retrieval-Augmented Generation) shopping assistant that answers product questions using hybrid search and structured LLM outputs. Features include a FastAPI backend, Streamlit chat UI, citation grounding, and RAGAS evaluation pipeline.

## ✨ Week 02 Highlights

- 🔍 **Hybrid Search**: Dense vector + BM25 sparse search with Reciprocal Rank Fusion (RRF)
- 📊 **Structured Outputs**: Type-safe LLM responses using Instructor library
- 🎯 **Citation Grounding**: Answers linked to specific products with images and prices
- 📝 **Prompt Templates**: Jinja2-based prompt management for easy iteration
- 📈 **Enhanced Observability**: Token tracking and detailed LangSmith traces

## Architecture

```
User → Streamlit UI (8501) → FastAPI (8000) → Qdrant (6333)
                                     ↓
                        OpenAI (embeddings + LLM w/ Instructor)
                                     ↓
                              LangSmith (tracing)
```

**Quick Links:**
- 📚 [CHANGELOG](CHANGELOG.md) - Release notes and version history
- 🏗️ [ARCHITECTURE](docs/ARCHITECTURE.md) - System design and diagrams
- 🔧 [TECHNICAL](docs/TECHNICAL.md) - Deep implementation details

**Services:**
- `streamlit-app` — chat interface with product suggestions at `http://localhost:8501`
- `api-app` — FastAPI RAG backend at `http://localhost:8000`
- `qdrant` — vector database with hybrid search at `http://localhost:6333`

**RAG Pipeline** (`apps/api`) - Week 02:
1. **Embed** the user query with `text-embedding-3-small` (OpenAI)
2. **Hybrid Search** - Combine dense vector + BM25 sparse search using RRF (weights: [3, 1])
3. **Retrieve** top-5 products from `Amazon-shopping-collection-01-hybrid-search` collection
4. **Build Prompt** using Jinja2 templates with product context
5. **Generate** structured answer with product citations using Instructor + `gpt-5.4-nano`
6. **Enrich** response with product images, prices, and details from Qdrant

## Project Structure

```
ai-shopping-assistant-lab/
├── apps/
│   ├── api/                        # FastAPI RAG service
│   │   ├── src/api/
│   │   │   ├── agents/
│   │   │   │   ├── agents.py       # LLM runners (OpenAI, Google)
│   │   │   │   └── retrieval_generation.py  # RAG pipeline
│   │   │   ├── api/
│   │   │   │   ├── endpoints.py    # POST /rag endpoint
│   │   │   │   └── models.py       # RAGRequest / RAGResponse
│   │   │   ├── core/config.py      # Env-based config
│   │   │   └── app.py              # FastAPI app entry point
│   │   ├── evals/eval_retriever.py # RAGAS evaluation script
│   │   └── Dockerfile
│   └── chat_bot_ui/                # Streamlit chat UI
│       ├── src/chat_bot_ui/
│       │   ├── core/config.py
│       │   └── app.py              # Streamlit app
│       └── Dockerfile
├── docker-compose.yml
├── pyproject.toml                  # uv workspace root
└── .env                            # API keys (not committed)
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [uv](https://docs.astral.sh/uv/) (for local development)
- Python 3.13+

## Setup

1. **Clone the repo and create a `.env` file** in the project root:

   ```env
   OPENAI_API_KEY=sk-...
   GOOGLE_API_KEY=...
   GROQ_API_KEY=...
   LANGSMITH_API_KEY=...        # optional, for tracing
   LANGSMITH_TRACING=true       # optional
   ```

2. **⚠️ Week 02 Update**: Populate Qdrant with **hybrid search collection**
   
   Create collection `Amazon-shopping-collection-01-hybrid-search` with:
   - Dense vectors: `text-embedding-3-small` (size: 1536, distance: Cosine)
   - Sparse vectors: `bm25` (built-in Qdrant BM25)
   
   See [TECHNICAL.md](docs/TECHNICAL.md#database-schema) for details.

## Running with Docker Compose

```bash
docker-compose up --build
```

Then open `http://localhost:8501` in your browser.

## Local Development

Install workspace dependencies with uv:

```bash
uv sync
```

Run the API:

```bash
cd apps/api/src
uvicorn api.app:app --reload --port 8000
```

Run the UI:

```bash
cd apps/chat_bot_ui/src
streamlit run chat_bot_ui/app.py
```

## API Reference

### `POST /rag`

**Request:**
```json
{
  "query": "What wireless headphones do you have?"
}
```

**Response (Week 02):**
```json
{
  "answer": "We have the following wireless headphones...",
  "used_context": [
    {
      "image_url": "https://m.media-amazon.com/images/...",
      "price": "79.99",
      "description": "Wireless over-ear headphones with..."
    }
  ]
}
```

**Key Changes from Week 01:**
- Added `used_context` array with product citations
- Each context item includes image URL, price, and description
- LLM responses now include structured product references

## Evaluation

The `apps/api/evals/eval_retriever.py` script evaluates retrieval quality using [RAGAS](https://docs.ragas.io/) against a LangSmith dataset (`Amazon-shopping-collection-01-dataset`).

**Metrics:**
- **ID-Based Context Precision** — are retrieved products relevant?
- **ID-Based Context Recall** — are all relevant products retrieved?
- **Faithfulness** — does the answer stay grounded in retrieved context?
- **Response Relevancy** — does the answer address the question?

Run the eval (requires a running Qdrant at `localhost:6333` and a populated LangSmith dataset):

```bash
uv run python apps/api/evals/eval_retriever.py
```

## Features

### Week 02 Enhancements

- **Hybrid Search with RRF**: Combines semantic understanding (dense vectors) with keyword precision (BM25)
  - Prefetch 20 candidates per method
  - Weighted fusion: 3x dense, 1x sparse
  - Optimal balance of recall and precision

- **Structured LLM Outputs**: Instructor library ensures type-safe, validated responses
  - Automatic retry on validation failures
  - Pydantic schemas for API contracts
  - Citations linked to retrieved products

- **Citation Grounding**: Every answer traceable to source products
  - Product IDs extracted from LLM response
  - Enriched with images, prices, and metadata
  - Visual product cards in UI sidebar

- **Prompt Management**: Jinja2 templates for maintainable prompts
  - Version-controlled YAML configurations
  - Easy A/B testing without code changes
  - Metadata tracking (author, version, description)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for embeddings and LLM generation |
| `GOOGLE_API_KEY` | Yes | For Google Gemini LLM (alternative provider) |
| `GROQ_API_KEY` | Yes | For Groq LLM (alternative provider) |
| `LANGSMITH_API_KEY` | No | Enables LangSmith tracing |
| `LANGSMITH_TRACING` | No | Set to `true` to enable tracing |

## Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture with diagrams
- **[docs/TECHNICAL.md](docs/TECHNICAL.md)** - Implementation deep-dive
  - Hybrid search details (RRF algorithm, weight selection)
  - Instructor integration (structured outputs, validation)
  - Prompt management (Jinja2 templates, best practices)
  - Database schema (Qdrant collection configuration)
  - Performance optimization strategies

## Migration from Week 01

⚠️ **Breaking Changes**:
- Collection name changed to `Amazon-shopping-collection-01-hybrid-search`
- Requires BM25 sparse vectors (re-indexing needed)
- API response includes new `used_context` field

See [CHANGELOG.md](CHANGELOG.md#migration-notes) for detailed migration guide.
