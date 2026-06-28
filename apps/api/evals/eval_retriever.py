from qdrant_client import QdrantClient
from langsmith import Client
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from api.agents.retrieval_generation import rag_pipeline
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import IDBasedContextPrecision, IDBasedContextRecall, Faithfulness, ResponseRelevancy

#--------------------------------------------------------------
ls_client = Client()
ragas_llm = LangchainLLMWrapper(ChatOpenAI(model="gpt-5.4-mini"))
ragas_embeddings = LangchainEmbeddingsWrapper(OpenAIEmbeddings(model="text-embedding-3-small"))
dataset_name = "Amazon-shopping-collection-01-dataset"
qdrant_client = QdrantClient(url="http://localhost:6333")
#--------------------------------------------------------------
def ragas_context_precision_id_based(run, example):
    print(f"run:{run}")
    print(f"example:{example}")
    print(f"retrieved_context_ids: {run.outputs["retrieved_context_ids"]}")
    print(f"reference_context_ids: {example.outputs["reference_context_ids"]}")
    sample = SingleTurnSample(
        retrieved_context_ids=run.outputs["retrieved_context_ids"],
        reference_context_ids=example.outputs["reference_context_ids"]
    )
    #print(sample)
    scorer = IDBasedContextPrecision()

    return scorer.single_turn_ascore(sample)
#--------------------------------------------------------------
def ragas_context_recall_id_based(run, example):
    print(f"run:{run}")
    print(f"example:{example}")
    sample = SingleTurnSample(
        retrieved_context_ids=run.outputs["retrieved_context_ids"],
        reference_context_ids=example.outputs["reference_context_ids"]
    )

    scorer = IDBasedContextRecall()

    return scorer.single_turn_ascore(sample)
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

    sample = SingleTurnSample(
            user_input=run.outputs["query"],
            response=run.outputs["answer"],
            retrieved_contexts=run.outputs["retrieved_context"]
        )

    scorer = Faithfulness(llm=ragas_llm)
    
    return scorer.single_turn_ascore(sample)
#--------------------------------------------------------------
def ragas_relevancy(run, example):
    print(f"run:{run}")
    sample = SingleTurnSample(
        user_input=run.outputs["query"],
        response=run.outputs["answer"],
        retrieved_contexts=run.outputs["retrieved_context"]
    )

    scorer = ResponseRelevancy(llm=ragas_llm, embeddings=ragas_embeddings)

    return scorer.single_turn_ascore(sample)
#--------------------------------------------------------------
results= ls_client.evaluate(
    lambda x: rag_pipeline(x["question"], qdrant_client),
    data=dataset_name,
    evaluators=[
        ragas_context_precision_id_based,
        ragas_context_recall_id_based
    ],
    experiment_prefix="retriever"
)
#--------------------------------------------------------------