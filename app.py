import uvicorn
import time
from fastapi import FastAPI
from pydantic import BaseModel, Field
from src.RAGFunctions import rag_chain, history_aware_retriever
from src.DatabaseFunctions import get_chat_history,get_sessions, insert_application_logs, create_application_logs
from src.Logger import get_logger
def get_response(session_id, query):
    if session_id in get_sessions():
        chat_history = get_chat_history(session_id)

    else:
        chat_history = []

    response = rag_chain.invoke({"input": query, "chat_history": chat_history, "context": history_aware_retriever})[
        "answer"]
    insert_application_logs(session_id, query, response)
    return response

# Initialize database
create_application_logs()

# Initialize logger
logger = get_logger()

# Create an instance of FastAPI
app = FastAPI()

# Define a Pydantic model for the POST request body
class Message(BaseModel):
    session: str = Field(..., max_length=10)  # String with maximum length of 10
    text: str = Field(..., min_length=10, max_length=500)  # String with length between 10 and 500



@app.get("/")
def home():
    logger.info("Root endpoint was accessed.")
    return {"message": "Welcome to health assist chat bot api"}

@app.post("/chat")
def get_answer(message: Message):
    start_time = time.time()
    session_id = message.session
    user_query = message.text
    response = get_response(session_id,user_query)
    end_time = time.time()
    response_time = end_time - start_time
    logger.info("Response was successful, session_id: %s, user_query: %s,response: %s, response_time: %d ms", session_id, user_query,response_time)
    return {"response":response}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8003)