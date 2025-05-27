import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def load_chunks(path="chunks_with_embeddings.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def build_vector_matrix(chunks):
    texts = [item["text"] for item in chunks]
    matrix = np.array([item["embedding"] for item in chunks])
    return texts, matrix

def search_best_chunk(question, client, chunks, matrix, threshold=0.15):
    q_emb = client.embeddings.create(
        input=question,
        model="text-embedding-3-small"
    ).data[0].embedding

    sims = cosine_similarity([q_emb], matrix)[0]
    idx = int(np.argmax(sims))
    if sims[idx] < threshold:
        return None
    return chunks[idx]
