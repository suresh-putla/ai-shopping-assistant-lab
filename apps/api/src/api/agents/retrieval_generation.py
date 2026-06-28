from openai import OpenAI
from qdrant_client import QdrantClient
from dotenv import load_dotenv
from langsmith import traceable, get_current_run_tree
from . import agents
#--------------------------------------------------------------
openai = OpenAI()

qdrant_collection_name="Amazon-shopping-collection-01"
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
@traceable( name = "retrieve_context" )
def retrieve_context(query, qdrant_client, k=5):

    query_embedding = get_embedding(query)
    results = qdrant_client.query_points(collection_name=qdrant_collection_name, query=query_embedding, limit=k)

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
@traceable( name = "process_context" )
def process_context(context):
    formated_context = ""
    for id, chunk, rating in zip(context['retrieved_context_ids'], context['retrieved_context'], context['retrieved_context_ratings']):
        formated_context += f"- ID: {id}, rating: {rating}, description: {chunk}\n"
    return formated_context
#--------------------------------------------------------------
@traceable( name = "build_prompt" )
def build_prompt(context, query):
    prompt = f"""
    You are a shopping assistant that can answer questions about the products in stock.

    You will be given a question and a list of context.

    Instructions:
    - answer the question based on the provided context only.
    - never use word context and refer to it as the available products.
    - do not use markdown formatting.
    - if you do not find any products, say 'there is no product in the stock'.

    Context:
    {context}

    Question:
    {query}
    """

    return prompt
#--------------------------------------------------------------
@traceable( name = "generate_answer", 
            run_type="llm", 
            metadata={'ls_model_provider':'openai', 'ls_model_name':'gpt-5.4-nano'}
            )
def generate_answer(prompt):
    messages=[{"role":"system","content": prompt}]
    response = agents.run_llm("openai", "gpt-5.4-nano", messages)
    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"]={
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }

    return response.choices[0].message.content
#--------------------------------------------------------------
@traceable( name = "rag_pipeline" )
def rag_pipeline(query, qdrant_client, top_k= 5):

    # retrieve chunks of ontext from RAG
    retrieved_context = retrieve_context(query, qdrant_client, top_k)

    # preprocessing chunks
    processed_context = process_context(retrieved_context)

    # build prompt
    prompt = build_prompt(processed_context, query)

    # generate response usign LLM
    llm_answer = generate_answer(prompt)

    final_answer= {
        "query": query,
        "answer": llm_answer,
        "retrieved_context_ids": retrieved_context['retrieved_context_ids'],
        "retrieved_context": retrieved_context['retrieved_context'],
    }
    return final_answer
#--------------------------------------------------------------
    