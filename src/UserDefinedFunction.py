from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)

class RAGFunctions:

    @staticmethod
    def vector_store(model_name,embedding_dim,cluster_uri,db_name,collection_name):
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

    @staticmethod
    def LLM_model(model_name):
        return ChatGoogleGenerativeAI(
            model=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

    @staticmethod
    def history_aware_retriever(llm,retriever):
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

        return create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

    @staticmethod
    def question_answer_chain(system_prompt,llm):
         #include context position as {context} format in system_prompt
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        return create_stuff_documents_chain(llm, qa_prompt)
