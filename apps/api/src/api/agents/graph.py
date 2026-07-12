
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Annotated, List
from operator import add
from api.agents.agents1 import RAGUsedContext
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import Send
from api.agents.agents1 import intent_router_node, agent_node, get_formatted_item_context
from qdrant_client import QdrantClient
from qdrant_client import models
from qdrant_client.models import VectorParams, Filter, FieldCondition, MatchValue, Distance, SparseVectorParams, Modifier, PayloadSchemaType, PointStruct, Document, Prefetch, FusionQuery

#--------------------------------------------------------------
class State(BaseModel):
    messages: Annotated[List[Any], add] = []
    question_relevant: bool = False
    iteration: int = 0
    answer: str = ""
    final_answer: bool = False
    references: list[RAGUsedContext] = []
#--------------------------------------------------------------
def tool_router(state: State) -> str:
    print(f"tool_router")
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

tools = [get_formatted_item_context]
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
def run_agent(question: str) -> dict:
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "iteration": 0
        
    }
    result = graph.invoke(initial_state)
    return result
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
def agent_wrapper(question: str) -> dict:
    qdrant_client = QdrantClient(url="http://qdrant:6333")
    result = run_agent(question)
    used_context = []
    for reference in result.get('references', []):
        payload = get_description(qdrant_client, reference["id"])
        image_url = payload.get("image","")
        price = str(payload.get("price",""))
        if image_url:
            used_context.append({"image_url":image_url, "price": price, "description": reference["description"]})

    return {
        "answer": result.get('answer', []),
        "used_context": used_context
    }
#--------------------------------------------------------------