import os
import re

def clean_text_for_splitting(text):
    text = text.replace("🔰", "").replace("🔶", "").replace("🔸", "")
    text = text.replace('\t', ' ')
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    text = re.sub(r'\s*\n\s*', '\n', text)  
    text = re.sub(r'[ \t]+', ' ', text)     
    return text.strip()

def split_into_chunks_hybrid(original_text, max_words_per_chunk=300, overlap_words=50):
    cleaned_text = clean_text_for_splitting(original_text)
    paragraphs = cleaned_text.split('\n\n') # Tách theo đoạn đã được chuẩn hóa
    final_chunks = []
    
    for para_text in paragraphs:
        para_text = para_text.strip()
        if not para_text: continue

        para_text_single_spaced = re.sub(r'\s+', ' ', para_text) # Chuẩn hóa space trong đoạn để đếm từ
        words_in_para = para_text_single_spaced.split()
        
        if len(words_in_para) <= max_words_per_chunk:
            # Nếu đoạn đủ ngắn, dùng text gốc của đoạn (có thể còn \n đơn)
            final_chunks.append(para_text) 
        else:
            # Nếu đoạn quá dài, chia theo từ (words_in_para đã là 1 dòng)
            step = max_words_per_chunk - overlap_words
            if step <= 0: step = max_words_per_chunk // 2 if max_words_per_chunk > 1 else 1
            for i in range(0, len(words_in_para), step):
                chunk_words = words_in_para[i : i + max_words_per_chunk]
                if not chunk_words: continue
                final_chunks.append(" ".join(chunk_words)) 
    return final_chunks

def read_all_txt_files(data_dir="data"):
    all_chunks_with_meta = []
    print(f"Đang đọc file từ thư mục: {data_dir}")
    files = sorted(os.listdir(data_dir)) # Sắp xếp để có thứ tự nhất quán
    for filename in files:
        if filename.endswith(".txt"):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    original_text = f.read()
                current_file_chunks_text = split_into_chunks_hybrid(original_text)
                for chunk_text_content in current_file_chunks_text:
                    # Quan trọng: Chuẩn hóa lần cuối mỗi chunk thành 1 dòng cho embedding
                    text_for_embedding_and_rag = re.sub(r'\s+', ' ', chunk_text_content).strip()
                    if text_for_embedding_and_rag: # Chỉ thêm nếu chunk không rỗng sau khi strip
                        all_chunks_with_meta.append({
                            "filename": filename,
                            "text": text_for_embedding_and_rag 
                        })
                print(f"  - Đã xử lý {filename} -> {len(current_file_chunks_text)} chunks được thêm vào.")
            except Exception as e:
                print(f"  - Lỗi khi đọc hoặc xử lý file {filename}: {e}")
    return all_chunks_with_meta

if __name__ == "__main__":
    chunks_list = read_all_txt_files(data_dir="data") 
    print(f"\nĐã tách thành công tổng cộng {len(chunks_list)} chunks.")