from pydantic import BaseModel
#--------------------------------------------------------------
class RAGRequest(BaseModel):
    query: str
#--------------------------------------------------------------
class RAGUsedContext(BaseModel):
    image_url: str
    price: str
    description: str
#--------------------------------------------------------------
class RAGResponse(BaseModel):
    answer: str
    used_context: list[RAGUsedContext]
#--------------------------------------------------------------