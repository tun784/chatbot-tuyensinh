import os
import re

def clean_text(text):
    """Làm sạch văn bản: xóa icon và chuẩn hóa khoảng trắng."""
    
    # Xóa các icon đã biết (có thể thêm các icon khác nếu cần)
    text = text.replace("🔰", "")
    text = text.replace("🔶", "")
    text = text.replace("🔸", "")
    
    # Loại bỏ các ký tự điều khiển không mong muốn (ngoại trừ newline và tab nếu bạn muốn giữ)
    # Giữ lại \n để split_into_chunks có thể hoạt động dựa trên từ
    # text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text) 

    # Thay thế nhiều lần xuống dòng liên tiếp bằng một ký tự xuống dòng duy nhất
    # Điều này giúp giữ lại cấu trúc đoạn văn nếu có
    text = re.sub(r'\n\s*\n', '\n', text) 
    
    # Thay thế tab bằng dấu cách
    text = text.replace('\t', ' ')

    # Thay thế nhiều khoảng trắng liên tiếp (bao gồm cả newline đã được giữ lại)
    # bằng một dấu cách duy nhất. Điều này quan trọng để .split() hoạt động đúng.
    text = re.sub(r'\s+', ' ', text) 
    
    return text.strip()

def split_into_chunks(text, max_words=300, overlap_words=50):
    """Tách văn bản thành các chunk nhỏ hơn với độ trùng lặp."""
    words = text.split()
    chunks = []

    step = max_words - overlap_words
    if step <= 0:
        step = max_words // 2 if max_words > 1 else 1

    for i in range(0, len(words), step):
        chunk_words = words[i:i + max_words]
        if not chunk_words:
            continue
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
    return chunks

def read_all_txt_files(data_dir="data"):
    """Đọc tất cả file .txt, làm sạch và tách thành chunks."""
    all_chunks = []
    print(f"Đang đọc file từ thư mục: {data_dir}")
    files = sorted(os.listdir(data_dir)) # Sắp xếp để có thứ tự nhất quán
    for filename in files:
        if filename.endswith(".txt"):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                    cleaned_text = clean_text(text) # Làm sạch
                    chunks = split_into_chunks(cleaned_text) # Tách
                    for chunk_text in chunks:
                        all_chunks.append({
                            "filename": filename,
                            "text": chunk_text
                        })
                print(f"  - Đã xử lý {filename} -> {len(chunks)} chunks")
            except Exception as e:
                print(f"  - Lỗi khi đọc file {filename}: {e}")
    return all_chunks

if __name__ == "__main__":
    chunks = read_all_txt_files()
    print(f"\nĐã tách thành công tổng cộng {len(chunks)} chunks.")