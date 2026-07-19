
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Annotated, List
from operator import add
from api.agents.agents1 import RAGUsedContext
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Send
from api.agents.agents1 import intent_router_node, agent_node, get_formatted_item_context, get_formatted_reviews_context
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import VectorParams, Filter, FieldCondition, MatchValue, Distance, SparseVectorParams, Modifier, PayloadSchemaType, PointStruct, Document, Prefetch, FusionQuery
from langgraph.checkpoint.postgres import PostgresSaver
import json
#--------------------------------------------------------------
class State(BaseModel):
    messages: Annotated[List[Any], add] = []
    question_relevant: bool = False
    iteration: int = 0
    answer: str = ""
    final_answer: bool = False
    references: list[RAGUsedContext] = []
    trace_id: str = ""
#--------------------------------------------------------------
def tool_router(state: State) -> str:
    if state.final_answer:
        return "end"
    elif state.iteration > 2:
        return "end"
    elif len(state.messages[-1].tool_calls) > 0:
        return "tools"
    else:
        return "end"
#--------------------------------------------------------------
def intent_router_conditional_edges(state: State) -> str:
    if state.question_relevant:
        return "agent_node"
    else:
        return "end"
#--------------------------------------------------------------
workflow = StateGraph(State)
workflow.add_node("intent_router_node", intent_router_node)
workflow.add_node("agent_node", agent_node)

tools = [get_formatted_item_context, get_formatted_reviews_context]
tool_node = ToolNode(tools)
workflow.add_node("tool_node", tool_node)
workflow.add_conditional_edges(
    "intent_router_node",
    intent_router_conditional_edges,
    {
        "agent_node": "agent_node",
        "end": END
    }
)
workflow.add_conditional_edges(
    "agent_node",
    tool_router,
    {
        "tools": "tool_node",
        "end": END
    }
)

workflow.add_edge(START, "intent_router_node")
workflow.add_edge("tool_node", "agent_node")

graph = workflow.compile()
#--------------------------------------------------------------
qdrant_collection_name="Amazon-shopping-collection-01-hybrid-search"
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
    return rcd[0].payload
#--------------------------------------------------------------
def _process_graph_event(chunk):

    def _is_node_start(chunk):
        return chunk[1].get("type") == "task"

    def _tool_to_text(tool_call):
        if tool_call.get("name") == "get_formatted_item_context":
            return f"Looking for items: {tool_call.get('args').get('query', '')}."
        elif tool_call.get("name") == "get_formatted_reviews_context":
            return f"Fetching user reviews..."

    if _is_node_start(chunk):
        if chunk[1].get("payload", {}).get("name") == "intent_router_node":
            return ("Analysing the question...")
        if chunk[1].get("payload", {}).get("name") == "agent_node":
            return ("Planning...")
        if chunk[1].get("payload", {}).get("name") == "tool_node":
            message = " ".join([_tool_to_text(tool_call) for tool_call in chunk[1].get('payload', {}).get('input', {}).messages[-1].tool_calls])
            return (message)
#--------------------------------------------------------------            
def agent_stream_wrapper(question: str, thread_id: str) -> dict:

    def _string_for_sse(str):
        return f"data: {str}\n\n"

    initial_state = {
        "messages": [HumanMessage(content=question)],
        "iteration": 0
    }
    
    config = { "configurable": {"thread_id": thread_id}}
    with PostgresSaver.from_conn_string("postgresql://langgraph_user:langgraph_password@postgres:5432/langgraph_db") as checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)
        #result = graph.invoke(initial_state, config)

        for chunk in graph.stream(initial_state,  config, stream_mode=["debug", "values"]):
            processed_chunk = _process_graph_event(chunk)

            # will be None if processed_chunk is not start of node. Yield if it is not None
            if processed_chunk:
                yield _string_for_sse(processed_chunk) #converting to server send event format..this is needed for streaming
            
            if chunk[0] == 'values':
                result = chunk[1]

    qdrant_client = QdrantClient(url="http://qdrant:6333")
    used_context = []
    for reference in result.get('references', []):
        payload = get_description(qdrant_client, reference["id"])
        image_url = payload.get("image","")
        price = str(payload.get("price",""))
        if image_url:
            used_context.append({"image_url":image_url, "price": price, "description": reference["description"]})

    yield _string_for_sse(json.dumps(
        {
        "type": "final_answer",
        "data":{
            "answer": result.get('answer', []),
            "used_context": used_context,
            "trace_id": result.get('trace_id', [])
        }
        })
    )
#--------------------------------------------------------------