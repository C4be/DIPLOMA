Пример запроса обращения к сервису Embeddings

```py
import asyncio
import httpx

async def main():
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # Пример 1: Запрос для документов (passages)
        doc_data = {
            "texts": [
                "Текст первого важного документа.",
                "Инструкция по эксплуатации микроволновки."
            ]
        }
        response_docs = await client.post(f"{base_url}/embed/documents", json=doc_data)
        docs_embeddings = response_docs.json()["embeddings"]
        print(f"Получено эмбеддингов документов: {len(docs_embeddings)}")

        # Пример 2: Запрос для поискового запроса (query)
        query_data = {"text": "Как разогреть еду?"}
        response_query = await client.post(f"{base_url}/embed/query", json=query_data)
        query_embedding = response_query.json()["embedding"]
        print(f"Размерность вектора запроса: {len(query_embedding)}")

if __name__ == "__main__":
    asyncio.run(main())

```