import json
import numpy as np
from openai import OpenAI
import os
from sklearn.metrics.pairwise import cosine_similarity

# Load chunks và embeddings đã build sẵn
data = json.load(open("chunks.json", "r", encoding="utf-8"))
chunks = data["chunks"]
matrix = np.array(data["embeddings"])

# Tạo client để tính embedding câu hỏi
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def search_best_chunk_with_embedding(query, top_k=1):
    # 1. Tạo embedding cho query
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    q_emb = np.array(resp["data"][0]["embedding"]).reshape(1, -1)

    # 2. Tính cosine similarity
    sims = cosine_similarity(q_emb, matrix)[0]
    idx = int(np.argmax(sims))
    if sims[idx] < 0.2:   # bạn có thể điều chỉnh ngưỡng
        return None
    return chunks[idx]
