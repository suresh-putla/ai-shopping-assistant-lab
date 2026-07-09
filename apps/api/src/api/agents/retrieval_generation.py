from openai import OpenAI
import cohere
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from langsmith import traceable, get_current_run_tree
import instructor
from pydantic import BaseModel, Field
from qdrant_client import models
from qdrant_client.models import VectorParams, Filter, FieldCondition, MatchValue, Distance, SparseVectorParams, Modifier, PayloadSchemaType, PointStruct, Document, Prefetch, FusionQuery
from api.agents.utils.prompt_management import prompt_template_config
from . import agents
#--------------------------------------------------------------
openai = OpenAI()
qdrant_collection_name="Amazon-shopping-collection-01-hybrid-search"
#--------------------------------------------------------------
class RAGUsedContext(BaseModel):
    id: str = Field(description="The id of the item used to answer the question")
    description: str = Field(description="The description of the item used to answer the question")
    
class RAGGenerationResponseWithGrounding(BaseModel):
    answer: str = Field(description="The answer to the question")
    references: list[RAGUsedContext] = Field(description="List of items used to answer the question")
#--------------------------------------------------------------
@traceable(
    name = "get_embedding",
    run_type = "embedding",
    metadata= {
            "ls_model_provider": "openai",
            "ls_model_name": "text-embedding-3-small"
        }
)
def get_embedding(text, model="text-embedding-3-small"):
    response = openai.embeddings.create(input=text, model="text-embedding-3-small")
    return response.data[0].embedding
#--------------------------------------------------------------
@traceable( name = "retrieve_data" )
def retrieve_data(query, qdrant_client, k=5, hybrid=True):

    query_embedding = get_embedding(query)
    
    if hybrid:
        # Sprint 1 : lesson 5 - Weighted RRF
        results = qdrant_client.query_points(
            collection_name=qdrant_collection_name, 
            prefetch = [
                Prefetch(query = query_embedding, using = "text-embedding-3-small", limit = 20),
                Prefetch(query = Document(text=query, model = "qdrant/bm25"), using = "bm25", limit = 20)
            ],
            query=models.RrfQuery(rrf = models.Rrf(weights=[3,1])),
            limit=k)
    else:
         # Sprint 1 : lesson 5 - Weighted RRF
        results = qdrant_client.query_points(
            collection_name=qdrant_collection_name, 
            query = query_embedding,
            using = "text-embedding-3-small",
            limit=k)

    retrieved_context_ids = []
    retrieved_context = []
    similarity_scores = []
    retrieved_context_ratings = []

    for pts in results.points:
        retrieved_context_ids.append(pts.payload['parent_asin'])
        retrieved_context.append(pts.payload['preprocessed_description'])
        similarity_scores.append(pts.score)
        retrieved_context_ratings.append(pts.payload['average_rating'])
        
    return {
        'retrieved_context_ids': retrieved_context_ids,
        'retrieved_context': retrieved_context,
        'similarity_scores': similarity_scores,
        'retrieved_context_ratings': retrieved_context_ratings
    }
#--------------------------------------------------------------
@traceable( name = "rerank_data",
   run_type = "tool")
def rerank_data(query, context, top_k):
    cohere_client = cohere.ClientV2()
    response = cohere_client.rerank(
        model="rerank-v4.0-pro",
        query=query,
        documents = context["retrieved_context"],
        top_n = top_k
    )
    order = [result.index for result in response.results]
    return {
         'retrieved_context_ids': [ context["retrieved_context_ids"][i] for i in order ],
        'retrieved_context': [ context["retrieved_context"][i] for i in order ],
        'similarity_scores': [ context["similarity_scores"][i] for i in order ],
        'retrieved_context_ratings': [ context["retrieved_context_ratings"][i] for i in order ]
    }

#--------------------------------------------------------------
@traceable( name = "process_context",
            run_type = "prompt")
def process_context(context):
    formated_context = ""
    for id, chunk, rating in zip(context['retrieved_context_ids'], context['retrieved_context'], context['retrieved_context_ratings']):
        formated_context += f"- ID: {id}, rating: {rating}, description: {chunk}\n"
    return formated_context
#--------------------------------------------------------------
@traceable( name = "build_prompt" )
def build_prompt(context, query):
    #prompt = f"""
    #You are a shopping assistant that can answer questions about the products in stock.

    #You will be given a question and a list of context.

    #Instructions:
    #- answer the question based on the provided context only.
    #- never use word context and refer to it as the available products.
    #- do not use markdown formatting.
    #- if you do not find any products, say 'there is no product in the stock'.

    #Context:
    #{context}

    #Question:
    #{query}
    #"""

    template = prompt_template_config("api/agents/prompts/retrieval_generation.yml", "retrieval_generation")
    prompt = template.render(context=context,query=query)
    return prompt
#--------------------------------------------------------------
@traceable( name = "generate_answer", 
            run_type="llm", 
            metadata={'ls_model_provider':'openai', 'ls_model_name':'gpt-5.4-nano'}
            )
def generate_answer(prompt):
    client = instructor.from_provider("openai/gpt-5.4-nano", mode=instructor.Mode.RESPONSES_TOOLS)

    messages=[{"role":"system","content": prompt}]
    #response = agents.run_llm("openai", "gpt-5.4-nano", messages)
   
    response, raw_response = client.create_with_completion(messages=messages, 
    reasoning={"effort": "none"},
    response_model=RAGGenerationResponseWithGrounding
    )

    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"]={
            "input_tokens": raw_response.usage.input_tokens,
            "output_tokens": raw_response.usage.output_tokens,
            "total_tokens": raw_response.usage.total_tokens
        }

    return response
#--------------------------------------------------------------
@traceable( name = "rag_pipeline" )
def rag_pipeline(query, qdrant_client, top_k= 5, hybrid = True, rerank=False, retrieve_k=20):

    # retrieve chunks of ontext from RAG
    retrieved_context = retrieve_data(
                                            query, 
                                            qdrant_client, 
                                            k = retrieve_k if rerank else top_k, 
                                            hybrid = hybrid)

    if rerank:
        retrieved_context = rerank_data(query, retrieved_context, top_k)

    # preprocessing chunks
    processed_context = process_context(retrieved_context)

    # build prompt
    prompt = build_prompt(processed_context, query)

    # generate response usign LLM
    llm_answer = generate_answer(prompt)

    final_answer= {
        "query": query,
        "answer": llm_answer.answer,
        "references": llm_answer.references,
        "retrieved_context_ids": retrieved_context['retrieved_context_ids'],
        "retrieved_context": retrieved_context['retrieved_context'],
    }
    return final_answer
#--------------------------------------------------------------
def get_description(qdrant_client, parent_asin: str) -> dict:
    
    rcd = qdrant_client.scroll(
        collection_name=qdrant_collection_name,
        with_payload=True,
        with_vectors=False,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="parent_asin",
                    match=MatchValue(value=parent_asin)
                )
            ]
        )
    )[0]
    print(f"--------------{rcd}")
    print(f"--------------{rcd[0].payload}")
    return rcd[0].payload
#--------------------------------------------------------------
def rag_pipeline_wrapper(query, top_k=5):
    qdrant_client = QdrantClient(url="http://qdrant:6333")
    result = rag_pipeline(query, qdrant_client, top_k)
    used_context = []
    for reference in result.get('references', []):
        payload = get_description(qdrant_client, reference.id)
        image_url = payload.get("image","")
        price = str(payload.get("price",""))
        if image_url:
            used_context.append({"image_url":image_url, "price": price, "description": reference.description})
    print(f"---------used_context: {used_context}")
    return {
        "answer": result.get('answer', []),
        "used_context": used_context
    }
#--------------------------------------------------------------
    