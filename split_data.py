# split_data.py (Phiên bản mới đọc JSON và chia chunk thông minh hơn)
import os
import json
import re

def clean_text_for_splitting(text):
    """Làm sạch cơ bản trước khi chia: xóa icon, chuẩn hóa space/newline."""
    # Thay thế các icon đã biết bằng một dấu cách để tránh dính từ
    text = text.replace("🔰", " ").replace("🔶", " ").replace("🔸", " ")
    # Loại bỏ các emoji khác bằng regex, thay bằng dấu cách
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002700-\U000027BF"  # Dingbats
        # Bỏ các dải unicode rộng có thể xóa chữ Việt nếu không cẩn thận
        # "\U000024C2-\U0001F251"
        # "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub(r' ', text)

    text = text.replace('\t', ' ')
    # Chuẩn hóa nhiều dòng trống thành 2 newline (để đánh dấu đoạn)
    text = re.sub(r'\n\s*\n', '\n\n', text) 
    # Chuẩn hóa các newline đơn lẻ (xóa space xung quanh)
    text = re.sub(r'\s*\n\s*', '\n', text)  
    # Chuẩn hóa nhiều space thành 1 space (không ảnh hưởng \n)
    text = re.sub(r'[ \t]+', ' ', text)     
    return text.strip()

def split_text_into_chunks(original_text, filename="unknown", max_words_per_chunk=200, overlap_words=40):
    """
    Chia văn bản thành các chunk. Ưu tiên chia theo đoạn (đánh dấu bằng '\n\n').
    Nếu đoạn quá dài, sẽ chia đoạn đó theo số từ.
    Các chunk cuối cùng sẽ được chuẩn hóa thành một dòng duy nhất.
    """
    cleaned_text_with_paragraphs = clean_text_for_splitting(original_text)
    # paragraphs = cleaned_text_with_paragraphs.split('\n\n') 
    paragraphs = original_text.split('\n\n') 
    
    final_chunks_text_only = []
    
    for para_text in paragraphs:
        para_text_stripped = para_text.strip()
        if not para_text_stripped:
            continue

        # Để đếm từ, chuẩn hóa đoạn văn thành một dòng duy nhất các từ
        para_text_single_spaced_for_word_count = re.sub(r'\s+', ' ', para_text_stripped)
        words_in_para = para_text_single_spaced_for_word_count.split()
        
        # Điều chỉnh max_words cho các file quan trọng
        current_max_words = max_words_per_chunk
        if "gioi-thieu-chung.txt" in filename or "cac-nganh-dao-tao.txt" in filename:
            current_max_words = 150 # Chunk nhỏ hơn cho file chung
        elif "thu-tuc-nhap-hoc.txt" in filename:
            current_max_words = 180

        if len(words_in_para) <= current_max_words:
            # Nếu đoạn đủ ngắn, chuẩn hóa thành 1 dòng và thêm vào
            final_chunks_text_only.append(re.sub(r'\s+', ' ', para_text_stripped).strip())
        else:
            # Nếu đoạn quá dài, chia theo từ (sử dụng words_in_para đã là 1 dòng)
            step = current_max_words - overlap_words
            if step <= 0: step = current_max_words // 2 if current_max_words > 1 else 1

            for i in range(0, len(words_in_para), step):
                chunk_words = words_in_para[i : i + current_max_words]
                if not chunk_words: continue
                final_chunks_text_only.append(" ".join(chunk_words))
            
    return final_chunks_text_only

def process_json_data(json_file_path="data_collection.json"):
    """
    Đọc dữ liệu từ file JSON, làm sạch và tách thành chunks.
    """
    all_chunks_with_meta = []
    print(f"Đang đọc và xử lý file JSON: {json_file_path}")
    
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data_from_json = json.load(f)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {json_file_path}. Hãy chạy convert_txt_to_json.py trước.")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi: File {json_file_path} không chứa JSON hợp lệ.")
        return []

    found_gioi_thieu_chung = False
    for item in data_from_json:
        filename = item.get("filename", "unknown_file.txt")
        original_text = item.get("text_content", "")

        if filename == "gioi-thieu-chung.txt":
            found_gioi_thieu_chung = True

        if not original_text:
            print(f"  - Bỏ qua file {filename} vì không có nội dung.")
            continue
            
        # Chia text của file hiện tại thành các chunks
        current_file_text_chunks = split_text_into_chunks(original_text, filename=filename)
        
        chunks_added_this_file = 0
        for chunk_text in current_file_text_chunks:
            if chunk_text: # Chỉ thêm nếu chunk không rỗng sau khi strip
                all_chunks_with_meta.append({
                    "filename": filename,
                    "text": chunk_text  # chunk_text đã được chuẩn hóa thành 1 dòng
                })
                chunks_added_this_file += 1
        print(f"  - Đã xử lý {filename} -> {chunks_added_this_file} chunks được thêm vào.")

    if not found_gioi_thieu_chung:
        print("CẢNH BÁO QUAN TRỌNG: Không tìm thấy 'gioi-thieu-chung.txt' trong file JSON.")
        print("Các câu hỏi về địa chỉ, học phí có thể không được trả lời chính xác.")
        
    return all_chunks_with_meta

if __name__ == "__main__":
    # Bước 1: Chạy convert_txt_to_json.py để tạo data_collection.json (nếu chưa có hoặc muốn cập nhật)
    # convert_txt_to_json(data_dir="data", output_json_file="data_collection.json") # Bỏ comment nếu muốn chạy luôn ở đây

    # Bước 2: Đọc từ data_collection.json và tạo chunks
    chunks_list = process_json_data(json_file_path="data_collection.json") 
    print(f"\nĐã tách thành công tổng cộng {len(chunks_list)} chunks từ file JSON.")

    # In ra thử vài chunk đầu tiên từ gioi-thieu-chung.txt để kiểm tra
    print("\n--- Sample chunks from gioi-thieu-chung.txt (nếu có) ---")
    count = 0
    for chk in chunks_list:
        if chk["filename"] == "gioi-thieu-chung.txt":
            print(f"\nChunk {count+1} (từ gioi-thieu-chung.txt):")
            print(f"Text (first 300 chars): {chk['text'][:300]}...")
            count += 1
            if count >= 5: # In ra 5 chunk đầu tiên của file này
                break
    if count == 0:
        print("Không tìm thấy chunk nào từ gioi-thieu-chung.txt để in mẫu (có thể file không tồn tại trong JSON hoặc không có chunk nào được tạo).")