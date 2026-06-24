from langchain.embeddings.base import Embeddings
from sentence_transformers import SentenceTransformer
from settings import settings


class EmbeddingModel(Embeddings):
    """Класс для генерации эмбеддингов текстов с использованием префиксов."""
    
    def __init__(self, model_name=settings.embedding_model):
        self.model = SentenceTransformer(model_name)
        
    
    def embed_documents(self, texts):
        texts_with_prefix = ["passage: " + text for text in texts]
        embeddings = self.model.encode(texts_with_prefix, normalize_embeddings=True)
        return embeddings.tolist()


    def embed_query(self, text):
        text_with_prefix = "query: " + text
        embedding = self.model.encode(text_with_prefix, normalize_embeddings=True)
        return embedding.tolist()
    