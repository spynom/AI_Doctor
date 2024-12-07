from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
import os
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from dotenv import load_dotenv
load_dotenv()


#connect to Mongodb Database
model_name = "all-MiniLM-L6-v2"
embedding_dim = 384
cluster_uri =os.getenv("CLUSTER_URL")
db_name = "langchain"
collection_name = "vector"





def vector_store():
    embeddings = SentenceTransformerEmbeddings(model_name=model_name)

    # initialize MongoDB python client
    client = MongoClient(cluster_uri)
    ATLAS_VECTOR_SEARCH_INDEX_NAME = "langchain-test-index-vectorstores"

    MONGODB_COLLECTION = client[db_name][collection_name]

    vector_store = MongoDBAtlasVectorSearch(
        collection=MONGODB_COLLECTION,
        embedding=embeddings,
        index_name=ATLAS_VECTOR_SEARCH_INDEX_NAME,
        relevance_score_fn="cosine",
    )

    return vector_store


def LLM_model(model_name):
    return ChatGoogleGenerativeAI(
        model=model_name,
        safety_settings={
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
    )


#connect to Mongodb Database
vector_store_ = vector_store()

# passing vector_store as retriever
retriever = vector_store_.as_retriever(search_kwargs={"k": 3})

# llm api
model_name = "gemini-1.5-pro-latest"
llm_model = LLM_model(model_name)

# history aware retriever for sending history chat data to llm
contextualize_q_system_prompt = """
        Given a chat history and the latest user question
        which might reference context in the chat history,
        formulate a standalone question which can be understood
        without the chat history. Do NOT answer the question,
        just reformulate it if needed and otherwise return it as is.
        """

contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)

history_aware_retriever = create_history_aware_retriever(
    llm_model, retriever, contextualize_q_prompt
)

# question and answer retriever
system_prompt = (
            """
            You are a health adviser bot. Your role is to provide accurate,
            context-based information related to health, wellness, and medical concerns.
            Always respond in a clear, professional, and empathetic tone. You should only
            offer general advice and guidance, and never diagnose, treat, or provide
            specific medical recommendations. Always encourage users to seek advice from
            licensed healthcare professionals for any specific medical issues. Ensure that
            any information does not encourage harmful
            practices. If unsure about a query, provide a general response and advise consulting
            a healthcare provider.
            """
            "\n\n"
            "{context}"
        )
# include context position as {context} format in system_prompt
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm_model, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

