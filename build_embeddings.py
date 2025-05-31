# build_embeddings.py (Cập nhật để dùng chunks từ process_json_data)
import google.generativeai as genai
import os
import json
# Thay đổi import:
from split_data import process_json_data # <--- THAY ĐỔI Ở ĐÂY
from tqdm import tqdm

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def build_embedding(text):
    resp = genai.embed_content(
        model="models/text-embedding-004",
        content=text,
        task_type="retrieval_document"
    )
    return resp['embedding']

if __name__ == "__main__":
    # Gọi hàm mới từ split_data.py để lấy chunks từ file JSON
    chunks = process_json_data(json_file_path="data_collection.json") # <--- THAY ĐỔI Ở ĐÂY
    
    if not chunks:
        print("Không có chunks nào được tạo từ file JSON. Dừng build_embeddings.")
    else:
        output = []
        for chunk_info in tqdm(chunks, desc="Đang tạo embedding"):
            # Đảm bảo lấy đúng key chứa text của chunk
            text_to_embed = chunk_info.get("text") 
            if text_to_embed is None:
                print(f"Cảnh báo: Chunk từ file {chunk_info.get('filename')} không có trường 'text'. Bỏ qua.")
                continue

            embedding = build_embedding(text_to_embed)
            output.append({
                "filename": chunk_info.get("filename"),
                "text": text_to_embed,
                "embedding": embedding
            })

        with open("chunks_with_embeddings.json", "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print("Đã lưu chunks_with_embeddings.json")