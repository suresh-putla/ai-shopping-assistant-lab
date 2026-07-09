from qdrant_client import QdrantClient
from langsmith import Client
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings import OpenAIEmbeddings
from api.agents.retrieval_generation import rag_pipeline
from ragas.metrics.collections import Faithfulness, AnswerRelevancy
#--------------------------------------------------------------
ls_client = Client()
#ragas_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-5.4-mini"))
openai_client = AsyncOpenAI()
ragas_llm = llm_factory(model="gpt-4.1-mini", client=openai_client, max_tokens=4000 )
ragas_embeddings = OpenAIEmbeddings(client=openai_client, model="text-embedding-3-small")
dataset_name = "Amazon-shopping-collection-01-dataset"
qdrant_client = QdrantClient(url="http://localhost:6333")
#--------------------------------------------------------------
def context_precision_id_based(run, example):
    print(f"run:{run}")
    print(f"example:{example}")
    print(f"retrieved_context_ids: {run.outputs["retrieved_context_ids"]}")
    print(f"reference_context_ids: {example.outputs["reference_context_ids"]}")

    retrieved_context_ids = { str(id) for id in run.outputs["retrieved_context_ids"]}
    reference_context_ids = { str(id) for id in example.outputs["reference_context_ids"]}
   #print(sample)
    score = len(retrieved_context_ids & reference_context_ids) / len(retrieved_context_ids ) if retrieved_context_ids else 0.0

    return score
#--------------------------------------------------------------
def context_recall_id_based(run, example):
    print(f"run:{run}")
    print(f"example:{example}")
    retrieved_context_ids = { str(id) for id in run.outputs["retrieved_context_ids"]}
    reference_context_ids = { str(id) for id in example.outputs["reference_context_ids"]}
   #print(sample)
    score = len(retrieved_context_ids & reference_context_ids) / len(reference_context_ids ) if reference_context_ids else 0.0

    return score
#--------------------------------------------------------------
def ragas_faithfulness(run, example):
    print(f"run:{run}")
    print("----------------")
    print(f"Query:{run.outputs["query"]}")
    print("----------------")
    print(f"answer:{run.outputs["answer"]}")
    print("----------------")
    print(f"retrieved_contexts:{run.outputs["retrieved_context"]}")
    print("----------------")
    for rc in run.outputs["retrieved_context"]:
        print(f"RC:{rc}")

    scorer = Faithfulness(llm=ragas_llm)
    result = scorer.score(
        user_input=run.outputs["query"],
        response=run.outputs["answer"],
        retrieved_contexts=run.outputs["retrieved_context"]
    )
  
    return result.value
#--------------------------------------------------------------
def ragas_relevancy(run, example):
    print(f"run:{run}")

    scorer = AnswerRelevancy(llm=ragas_llm, embeddings=ragas_embeddings)
    result = scorer.score(
         user_input=run.outputs["query"],
        response=run.outputs["answer"]
    )
    return result._value
#--------------------------------------------------------------
# print("Evaluating Plain Retreiver")
# results= ls_client.evaluate(
#     lambda x: rag_pipeline(x["question"], qdrant_client, top_k = 10, hybrid=False, rerank=False),
#     data="rag-evaluation-dataset-extended",
#     evaluators=[
#         context_precision_id_based,
#         context_recall_id_based,
#         # ragas_faithfulness,
#         # ragas_relevancy
#     ],
#     experiment_prefix="plain-retriever",
#     max_concurrency=10
# )
# #--------------------------------------------------------------
# print("Evaluating Hybrid Retreiver")
# results= ls_client.evaluate(
#     lambda x: rag_pipeline(x["question"], qdrant_client, top_k = 10, hybrid=True, rerank=False),
#     data="rag-evaluation-dataset-extended",
#     evaluators=[
#         context_precision_id_based,
#         context_recall_id_based,
#         # ragas_faithfulness,
#         # ragas_relevancy
#     ],
#     experiment_prefix="hybrid-retriever",
#     max_concurrency=10
# )
#--------------------------------------------------------------
print("Evaluating Hybrid Retreiver with reranking")
results= ls_client.evaluate(
    lambda x: rag_pipeline(x["question"], qdrant_client, top_k = 10, hybrid=True, rerank=True),
    data="rag-evaluation-dataset-extended",
    evaluators=[
        context_precision_id_based,
        context_recall_id_based,
        # ragas_faithfulness,
        # ragas_relevancy
    ],
    experiment_prefix="hybrid-rerank-retriever"
)