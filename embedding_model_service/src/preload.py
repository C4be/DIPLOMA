from sentence_transformers import SentenceTransformer
import os

# Указываем дефолтную модель, которую хотим запечь
model_name = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
print(f"Pre-downloading model: {model_name}...")
SentenceTransformer(model_name)
print("Model downloaded successfully.")