import os
import json
import numpy as np
import openai
from split_data import split_text_into_chunks

# Thiết lập API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# 1. Chia data.txt thành chunks
chunks = split_text_into_chunks("data.txt", max_chunk_size=500)

# 2. Gọi OpenAI Embedding để tính vector cho từng chunk
embeddings = []
for chunk in chunks:
    resp = openai.Embedding.create(
        model="text-embedding-3-small",
        input=chunk
    )
    emb = resp["data"][0]["embedding"]
    embeddings.append(emb)

# 3. Lưu chunks + embeddings ra file
with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump({"chunks": chunks, "embeddings": embeddings}, f)
