import unittest
from langchain_community.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain_chroma import Chroma

class RAGTest(unittest.TestCase):
    def setUp(self):
        model_name = "all-MiniLM-L6-v2"
        embeddings = SentenceTransformerEmbeddings(model_name=model_name)
        self.vector_store = Chroma(
            collection_name="example_collection",
            embedding_function=embeddings,
            persist_directory="./chroma_langchain_db",
        )
    def test_similarity_search_over_db(self):
        results = self.vector_store.similarity_search(
            "when to eat salad?",
            k=3,
        )

        self.assertEqual(len(results), 3)

