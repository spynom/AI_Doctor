import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field
from UserDefinedFunction import DatabaseFunctions,RAGFunctions
import os
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from dotenv import load_dotenv
load_dotenv()

# create database instance
DatabaseFunctions.create_application_logs()

#connect to Mongodb Database
vector_store_ = RAGFunctions.vector_store()

# passing vector_store as retriever
retriever = vector_store_.as_retriever(search_kwargs={"k": 3})

# llm api
model_name = "gemini-1.5-pro-latest"
llm_model = RAGFunctions.LLM_model(model_name)

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

def get_response(session_id, query):
    if session_id in DatabaseFunctions.get_sessions():
        chat_history = DatabaseFunctions.get_chat_history(session_id)

    else:
        chat_history = []

    response = rag_chain.invoke({"input": query, "chat_history": chat_history, "context": history_aware_retriever})[
        "answer"]
    DatabaseFunctions.insert_application_logs(session_id, query, response)
    return response


# Create an instance of FastAPI
app = FastAPI()

# Define a Pydantic model for the POST request body
class Message(BaseModel):
    session: str = Field(..., max_length=10)  # String with maximum length of 10
    text: str = Field(..., min_length=10, max_length=500)  # String with length between 10 and 500



@app.get("/")
def home():
    return {"message": "Welcome to health assist chat bot api"}

@app.post("/chat")
def get_answer(message: Message):
    session = message.session
    question = message.text
    response = get_response(session,question)
    return {"response":response}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8003, reload=True)