import google.generativeai as genai # Thay thế từ openai
import os
import json
from split_data import read_all_txt_files
from tqdm import tqdm

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Đảm bảo biến môi trường này được đặt

def build_embedding(text):
    # Sử dụng model embedding của Google GenAI
    # Đảm bảo model "models/text-embedding-004" có trong list.py của bạn
    resp = genai.embed_content(
        model="models/text-embedding-004", # Model embedding của Google
        content=text,
        task_type="retrieval_document" # Task type cho tài liệu
    )
    return resp['embedding'] # Lấy trực tiếp phần embedding

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