import os
import json

def convert_txt_to_json(data_dir="data", output_json_file="data_collection.json"):
    """
    Đọc tất cả các file .txt trong data_dir và lưu vào một file JSON.
    Mỗi mục trong JSON sẽ có dạng: {"filename": "ten_file.txt", "text": "noi_dung_file"}
    """
    all_data = []
    print(f"Đang đọc file từ thư mục: {data_dir}")
    
    files = sorted(os.listdir(data_dir)) 
    for filename in files:
        if filename.endswith(".txt"):
            filepath = os.path.join(data_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text_content = f.read()
                all_data.append({
                    "filename": filename,
                    "text": text_content 
                })
                print(f"  - Đã đọc file: {filename}")
            except Exception as e:
                print(f"  - Lỗi khi đọc file {filename}: {e}")
                
    # Lưu tất cả dữ liệu vào một file JSON
    try:
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\nĐã lưu tất cả dữ liệu vào file: {output_json_file}")
        print(f"Tổng cộng có {len(all_data)} file được xử lý.")
    except Exception as e:
        print(f"Lỗi khi lưu file JSON: {e}")

if __name__ == "__main__":
    # Đảm bảo các file .txt của bạn nằm trong thư mục "data" (hoặc thư mục bạn chọn)
    # File JSON output sẽ được tạo ở thư mục hiện tại.
    convert_txt_to_json(data_dir="data", output_json_file="data_collection.json")