from openai import OpenAI
import os
import json
from split_data import read_all_txt_files
from tqdm import tqdm

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_embedding(text):
    resp = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return resp.data[0].embedding

if __name__ == "__main__":
    chunks = read_all_txt_files("data")
    output = []

    for chunk in tqdm(chunks, desc="🔍 Đang tạo embedding"):
        embedding = build_embedding(chunk["text"])
        output.append({
            "filename": chunk["filename"],
            "text": chunk["text"],
            "embedding": embedding
        })

    with open("chunks_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("✅ Đã lưu chunks_with_embeddings.json")
