import json
import numpy as np
import google.generativeai as genai
import os
from sklearn.metrics.pairwise import cosine_similarity

# Load chunks và embeddings đã build sẵn
data = json.load(open("chunks_with_embeddings.json", "r", encoding="utf-8"))
chunks = [item["text"] for item in data]
matrix = np.array([item["embedding"] for item in data])

# Tạo client để tính embedding câu hỏi
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def search_best_chunk_with_embedding(query):
    q_emb_result = genai.embed_content(model="models/text-embedding-004",
                                       content=query,
                                       task_type="retrieval_query")
    q_emb = np.array(q_emb_result['embedding']).reshape(1, -1)

    sims = cosine_similarity(q_emb, matrix)[0]
    idx = int(np.argmax(sims))

    # --- Thêm các dòng print sau đây để gỡ lỗi ---
    print(f"--- Debug Search Engine ---")
    print(f"Câu hỏi: {query}")
    print(f"Độ tương đồng cao nhất tìm được: {sims[idx]:.4f}")
    print(f"Chunk được chọn (index {idx}):")
    print(chunks[idx])
    print(f"-------------------------")
    # ---------------------------------------------

    if sims[idx] < 0.04:
        return None
    return chunks[idx]