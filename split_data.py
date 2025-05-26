import os

def split_text_into_chunks(text, max_words=400):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i : i + max_words])
        chunks.append(chunk)
    return chunks

def process_all_files(input_dir="raw_data", output_path="chunks.json"):
    all_chunks = []
    for fname in os.listdir(input_dir):
        if not fname.endswith(".txt"): continue
        with open(os.path.join(input_dir, fname), "r", encoding="utf-8") as f:
            text = f.read().strip()
        chunks = split_text_into_chunks(text, max_words=400)
        # lưu kèm thông tin nguồn nếu cần:
        for c in chunks:
            all_chunks.append({"source": fname, "text": c})
    # ghi ra JSON để bước build embeddings dùng:
    import json
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(all_chunks, out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    process_all_files()
