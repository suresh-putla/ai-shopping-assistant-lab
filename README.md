# AI Shopping Assistant Lab

A RAG-based shopping assistant that answers product questions using a vector database of Amazon product data. Includes a FastAPI backend, a Streamlit chat UI, and a RAGAS evaluation pipeline.

## Architecture

```
User → Streamlit UI (8501) → FastAPI (8000) → Qdrant (6333)
                                     ↓
                               OpenAI (embeddings + LLM)
                                     ↓
                              LangSmith (tracing)
```

**Services:**
- `streamlit-app` — chat interface at `http://localhost:8501`
- `api-app` — FastAPI RAG backend at `http://localhost:8000`
- `qdrant` — vector database at `http://localhost:6333`

**RAG pipeline** (`apps/api`):
1. Embed the user query with `text-embedding-3-small`
2. Retrieve top-5 product descriptions from the `Amazon-shopping-collection-01` Qdrant collection
3. Build a prompt with retrieved context
4. Generate an answer with `gpt-5.4-nano` via OpenAI

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

2. **Populate Qdrant** with Amazon product embeddings into the `Amazon-shopping-collection-01` collection before running the stack. (See your data ingestion notebook.)

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

```json
// Request
{ "query": "What wireless headphones do you have?" }

// Response
{ "answer": "We have the following wireless headphones..." }
```

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

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Used for embeddings and LLM generation |
| `GOOGLE_API_KEY` | Yes | For Google Gemini LLM (alternative provider) |
| `GROQ_API_KEY` | Yes | For Groq LLM (alternative provider) |
| `LANGSMITH_API_KEY` | No | Enables LangSmith tracing |
| `LANGSMITH_TRACING` | No | Set to `true` to enable tracing |
