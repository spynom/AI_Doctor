from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo import MongoClient
from langchain_core.prompts import MessagesPlaceholder
from langchain.chains import create_history_aware_retriever
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
import sqlite3
import os
from dotenv import load_dotenv


load_dotenv()


#connect to Mongodb Database
model_name = "all-MiniLM-L6-v2"
embedding_dim = 384
cluster_uri =os.getenv("CLUSTER_URL")
db_name = "langchain"
collection_name = "vector"


class RAGFunctions:

    @staticmethod
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

    @staticmethod
    def LLM_model(model_name):
        return ChatGoogleGenerativeAI(
            model=model_name,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )


class DatabaseFunctions:
    @staticmethod
    def get_db_connection():
        conn = sqlite3.connect("rag_app.db")
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def create_application_logs():
        conn = DatabaseFunctions.get_db_connection()
        conn.execute('''CREATE TABLE IF NOT EXISTS application_logs
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        user_query TEXT,
        response TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.close()

    @staticmethod
    def insert_application_logs(session_id, user_query, response):
        conn = DatabaseFunctions.get_db_connection()
        conn.execute('INSERT INTO application_logs (session_id, user_query, response) VALUES (?, ?, ?)',
                     (session_id, user_query, response))
        conn.commit()
        conn.close()

    @staticmethod
    def get_chat_history(session_id):
        conn = DatabaseFunctions.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_query, response FROM application_logs WHERE session_id = ? ORDER BY created_at',
                       (session_id,))
        messages = []
        for row in cursor.fetchall():
            messages.extend([
                {"role": "human", "content": row['user_query']},
                {"role": "ai", "content": row['response']}
            ])
        conn.close()
        return messages

    @staticmethod
    def get_sessions():
        conn = DatabaseFunctions.get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT session_id FROM application_logs')
        sessions = []
        for row in cursor.fetchall():
            sessions.append(row['session_id'])

        conn.close()
        return sessions

