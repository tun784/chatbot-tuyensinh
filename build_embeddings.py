import google.generativeai as genai
import os
import json
from split_data import read_all_txt_files
from tqdm import tqdm

genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Thêm dòng này

def build_embedding(text):
    # Sử dụng embedding model của Google
    result = genai.embed_content(model="models/text-embedding-004",
                                 content=text,
                                 task_type="retrieval_document")
    return result['embedding']


if __name__ == "__main__":
    chunks = read_all_txt_files("data")
    output = []

    for chunk in tqdm(chunks, desc="Đang tạo embedding"):
        embedding = build_embedding(chunk["text"])
        output.append({
            "filename": chunk["filename"],
            "text": chunk["text"],
            "embedding": embedding
        })

    with open("chunks_with_embeddings.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("Đã lưu chunks_with_embeddings.json")