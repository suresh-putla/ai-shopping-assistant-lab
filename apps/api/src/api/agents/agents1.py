from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, convert_to_openai_messages, AIMessage
from langsmith import traceable, get_current_run_tree
from pydantic import BaseModel, Field
import instructor
from api.agents.utils.prompt_management import prompt_template_config
from api.agents.tools import get_formatted_item_context, get_formatted_reviews_context
###############################################################
#LANGGRAPH - AGENTS
###############################################################
# Pydantic Models
#--------------------------------------------------------------
class RAGUsedContext(BaseModel):
    id: str = Field(description="ID of the item used to answer the question")
    description: str = Field(description="Description of the item used to answer the question")

class FinalResponse(BaseModel):
    """ call this tool when final answer is possible using available context """
    answer: str = Field(description="Answer to the question")
    references: list[RAGUsedContext] = Field(description="List of items used to answer the question")

class IntentRouterResponse(BaseModel):
    question_relevant: bool
    answer: str = Field(description="An answer to the question if the users question is not relevant to the products.")

#--------------------------------------------------------------
# Q&A Agent
#--------------------------------------------------------------
@traceable(name="agent_node", run_type="llm", metadata={"ls_provider": "openai","ls_model_name": "gpt-5.4-mini" })
def agent_node(state) -> dict:
    
    template = prompt_template_config("api/agents/prompts/qna_agent.yml", "qna_agent")
    prompt = template.render()

    llm = ChatOpenAI(model="gpt-5.4-mini", reasoning_effort="low", use_responses_api=True)
    llm_with_tools = llm.bind_tools(
        [get_formatted_item_context, get_formatted_reviews_context, FinalResponse],
        tool_choice="required"
    )

    response = llm_with_tools.invoke(
        [
            SystemMessage(content=prompt),
            *state.messages
        ]
    )
    current_run = get_current_run_tree()
    
    if current_run:
        current_run.metadata["usage_metadata"]={
            "input_tokens": response.usage_metadata["input_tokens"],
            "output_tokens": response.usage_metadata["output_tokens"],
            "total_tokens": response.usage_metadata["total_tokens"]
        }

    final_answer = False
    answer = ""
    references = []

    if len(response.tool_calls) > 0:
        for tool_call in response.tool_calls:
            if tool_call.get("name") == "FinalResponse":
                final_answer = True
                answer = tool_call.get("args").get("answer")
                references.extend(tool_call.get("args").get("references"))
                response = AIMessage(content = answer)

    return {
        "messages": [response],
        "final_answer": final_answer,
        "iteration": state.iteration + 1,
        "answer": answer,
        "references": references
    }
#--------------------------------------------------------------
# Intent Router
#--------------------------------------------------------------
@traceable(name="route_intent", run_type="llm", metadata={ "ls_provider": "openai","ls_model_name": "gpt-5.4-mini" })
def intent_router_node(state) -> dict:

    template = prompt_template_config("api/agents/prompts/intent_router_agent.yml", "intent_router_agent")
    prompt = template.render()

    messages = state.messages

    conversation = []
    conversation.append(convert_to_openai_messages(messages[-1]))

    instructor_client = instructor.from_provider("openai/gpt-5.4-mini", mode=instructor.Mode.RESPONSES_TOOLS)

    response, raw_response = instructor_client.create_with_completion(
        messages=[
            {"role": "system", "content": prompt},
            *conversation
        ],
        reasoning={"effort": "none"},
        response_model=IntentRouterResponse
    )

    current_run = get_current_run_tree()
    if current_run:
        current_run.metadata["usage_metadata"]={
            "input_tokens": raw_response.usage.input_tokens,
            "output_tokens": raw_response.usage.output_tokens,
            "total_tokens": raw_response.usage.total_tokens
        }
        trace_id = str(current_run.trace_id)
    else:
        trace_id = ""

    return {
        "question_relevant": response.question_relevant,
        "answer": response.answer,
        "trace_id": trace_id
    }
#--------------------------------------------------------------