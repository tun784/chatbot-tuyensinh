from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
import torch
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Khai báo các biến cần thiết
data_path = "dataset"
qdrant_persistent_path = "qdrant_vector_store" # Directory for Qdrant to store data
qdrant_collection_name = "admissions_collection"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"

# Định nghĩa kích thước chunk cho các loại file khác nhau
CHUNK_CONFIG = {
    "default": {"size": 2000, "overlap": 500}, # Kích thước mặc định cho các file ngành
    "gioi-thieu-chung.txt": {"size": 600, "overlap": 90},
    "thu-tuc-nhap-hoc.txt": {"size": 500, "overlap": 80},
    "diem-chuan-2024.txt": {"size": 500, "overlap": 80}
}
def get_chunk_config(filename):
    base_filename = os.path.basename(filename)
    return CHUNK_CONFIG.get(base_filename, CHUNK_CONFIG["default"])

def create_db_from_files():
    if not os.path.exists(data_path):
        print(f"Thư mục {data_path} không tồn tại")
        return
    
    print("Bắt đầu tạo vector store từ các file trong thư mục data")
    all_chunks = []
    file_paths = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith(".txt")]
    if not file_paths:
        print(f"Không tìm thấy file .txt nào trong thư mục {data_path}")
        
        return
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        print(f" Đang xử lý {filename} từ {data_path}...")
        try:
            loader = TextLoader(file_path, encoding="utf-8")
            documents = loader.load() # Load từng file một
            
            if not documents:
                print(f"    Không có nội dung trong file: {filename}")
                continue

            config = get_chunk_config(filename)
            current_chunk_size = config["size"]
            current_chunk_overlap = config["overlap"]
            
            print(f" Sử dụng chunk_size={current_chunk_size}, chunk_overlap={current_chunk_overlap} ")
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=current_chunk_size, 
                chunk_overlap=current_chunk_overlap
            )
            chunks_from_file = text_splitter.split_documents(documents)
            all_chunks.extend(chunks_from_file)
            print(f" Đã chia {filename} thành {len(chunks_from_file)} chunks.")
            
        except Exception as e:
            print(f" Lỗi khi xử lý file {filename}: {e}")

    if not all_chunks:
        print("Không có chunks nào được tạo. Dừng lại.")
        return
    else:
        print(f"\nTổng số đoạn đã chia từ tất cả các file: {len(all_chunks)}")

    print(f"Sử dụng mô hình nhúng: {model_sentence}")
    print(torch.cuda.get_device_name(0) + " đã được sử dụng." if torch.cuda.is_available() else "Không có GPU nào được phát hiện, sẽ sử dụng CPU.")

    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}  # Chạy bằng RTX 3050
    )
    
    print("Đang tạo vector store...")
    try:
        if not os.path.exists(qdrant_persistent_path):
            os.makedirs(qdrant_persistent_path, exist_ok=True)
            print(f"Đã tạo thư mục lưu trữ Qdrant: {qdrant_persistent_path}")
        db = Qdrant.from_documents(
            documents=all_chunks,
            embedding=embedding_model,
            path=qdrant_persistent_path, # For local, persistent storage
            collection_name=qdrant_collection_name,
            force_recreate=True, # Set to False if you want to append or update existing
        )
        print("Đã tạo vector store thành công.")
        print(f"Vector store Qdrant được lưu vào thư mục: {qdrant_persistent_path} với tên collection là: {qdrant_collection_name}")
    except Exception as e:
        print(f"Lỗi khi tạo hoặc lưu DB: {e}")
        return None
    return db

create_db_from_files()
