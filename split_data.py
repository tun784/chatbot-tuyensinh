import os
import re

def split_into_chunks(text, max_words=5000):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = " ".join(words[i:i+max_words])
        chunks.append(chunk)
    return chunks

def read_all_txt_files(data_dir="data"):
    all_chunks = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".txt"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
                chunks = split_into_chunks(text)
                for chunk in chunks:
                    all_chunks.append({
                        "filename": filename,
                        "text": chunk
                    })
    return all_chunks

if __name__ == "__main__":
    chunks = read_all_txt_files()
    print(f"Đã tách {len(chunks)} chunks.")
