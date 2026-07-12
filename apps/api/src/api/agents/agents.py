from openai import OpenAI
from google import genai
from api.core.config import config
import logging
#--------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
#--------------------------------------------------------------
openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
google_client = genai.Client(api_key=config.GOOGLE_API_KEY)
#--------------------------------------------------------------
def run_llm(provider, model_name, messages, max_tokens=500):
    if provider == "openai":
        return _run_llm_openai(model_name, messages, max_tokens)
    elif provider == "google":
        return _run_llm_google(model_name, messages)
#--------------------------------------------------------------
def _run_llm_openai(model_name, messages, max_tokens=500):
    response = openai_client.chat.completions.create(
        model=model_name, 
        messages=messages, 
        max_completion_tokens=max_tokens)
    return response
#--------------------------------------------------------------v
def _run_llm_google(model_name, messages):
    response = google_client.models.generate_content(
        model=model_name,
        contents=[message["content"] for message in messages]
    )
    return response
