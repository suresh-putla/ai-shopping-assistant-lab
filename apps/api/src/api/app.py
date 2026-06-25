from fastapi import FastAPI, Request
from pydantic import BaseModel

from openai import OpenAI
from google import genai
from api.core.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_llm(provider, model_name, messages, max_tokens=1000):
    if provider == "openai":
        client = OpenAI(api_key=config.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=max_tokens
        )
        return response.choices[0].message.content
    elif provider == "google":
        client = genai.Client(api_key=config.GOOGLE_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents=[message["content"] for message in messages]
        )
        return response.text


class ChatRequest(BaseModel):
    provider: str
    model_name: str
    messages: list[dict[str, str]]

class ChatResponse(BaseModel):
    message: str


app = FastAPI()

@app.post("/chat")
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    response = run_llm(payload.provider, payload.model_name, payload.messages)
    return ChatResponse(message=response)
