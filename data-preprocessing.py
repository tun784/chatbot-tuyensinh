import torch
import os
import csv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain_core.documents import Document
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Khai báo các biến cần thiết
data_path = "dataset"  # Thư mục chứa các file .txt
qdrant_persistent_path = "vector_store"  # Directory for Qdrant to store data
collection_path = "admissions_info"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"

# Định nghĩa kích thước chunk cho các loại file khác nhau
CHUNK_CONFIG = {
    "default": {"size": 3072, "overlap": 500}, # Kích thước mặc định cho các file ngành
    "gioi-thieu-chung.txt": {"size": 700, "overlap": 90},
    "thu-tuc-nhap-hoc.txt": {"size": 600, "overlap": 80},
}
def get_chunk_config(filename):
    base_filename = os.path.basename(filename)
    return CHUNK_CONFIG.get(base_filename, CHUNK_CONFIG["default"])

def create_db_from_files():
    print("Bắt đầu tạo vector store từ các file trong thư mục dataset (.txt và .csv)")
    all_chunks = []
    file_paths = [os.path.join(data_path, f) for f in os.listdir(data_path) if f.endswith(".txt") or f.endswith(".csv")]
    if not file_paths:
        print(f"Không tìm thấy file .txt hoặc .csv nào trong thư mục {data_path}")
        return
    for file_path in file_paths:
        filename = os.path.basename(file_path)
        print(f" Đang xử lý {filename} từ {data_path}...")
        try:
            if filename.endswith('.txt'):
                loader = TextLoader(file_path, encoding="utf-8")
                documents = loader.load()
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
            elif filename.endswith('.csv'):
                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # Tùy theo số cột, tạo mô tả phù hợp
                        if 'Điểm chuẩn' in row:  # 2023, 2024
                            text = f"Ngành {row['Tên ngành']} (Mã ngành: {row['Mã ngành']}), điểm chuẩn: {row['Điểm chuẩn']}, năm: {row.get('Năm', '')}"
                            all_chunks.append(Document(page_content=text, metadata={"nam": row.get("Năm", "")}))
                        elif 'Điểm chuẩn Điểm thi tốt nghiệp THPT' in row:  # 2022
                            text = (
                                f"Ngành {row['Tên ngành']} (Mã ngành: {row['Mã ngành']}), "
                                f"Điểm chuẩn thi tốt nghiệp THPT: {row['Điểm chuẩn Điểm thi tốt nghiệp THPT']}, "
                                f"Điểm chuẩn HB cả năm lớp 10, 11 & HK1 lớp 12: {row['Điểm chuẩn HB cả năm lớp 10, 11 & HK1 lớp 12']}, "
                                f"Điểm chuẩn HB cả năm lớp 12: {row['Điểm chuẩn HB cả năm lớp 12']}, "
                                f"Điểm chuẩn ĐGNL ĐHQG-HCM năm 2022: {row['Điểm chuẩn ĐGNL ĐHQG-HCM năm 2022']}, "
                                f"Điểm chuẩn xét tuyển thẳng theo đề án riêng: {row['Điểm chuẩn xét tuyển thẳng theo đề án riêng']}, "
                                f"năm: {row.get('Năm', '')}"
                            )
                            all_chunks.append(Document(page_content=text, metadata={"nam": row.get("Năm", "")}))
                        else:
                            text = str(row)
                            all_chunks.append(Document(page_content=text))
                print(f" Đã chuyển {filename} thành {len(list(reader))} documents.")
        except Exception as e:
            print(f" Lỗi khi xử lý file {filename}: {e}")

    if not all_chunks:
        print("Không có chunks nào được tạo. Dừng lại.")
        return
    else:
        print(f"\nTổng số đoạn đã chia/tạo từ tất cả các file: {len(all_chunks)}")

    print(f"Sử dụng mô hình nhúng: {model_sentence}")
    print(torch.cuda.get_device_name(0) + " đã được sử dụng." if torch.cuda.is_available() else "Không có GPU nào được phát hiện, sẽ sử dụng CPU.")

    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )
    print("Đang tạo vector store...")
    try:
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
            print(f"Đã tạo thư mục lưu trữ: {data_path}")
        db = Qdrant.from_documents(
            documents=all_chunks,
            embedding=embedding_model,
            path=qdrant_persistent_path,
            collection_name=collection_path,
            force_recreate=True, # Set to False if you want to append or update existing
        )
        print("Đã tạo vector store thành công.")
        print(f"Vector store Qdrant được lưu với tên collection là: {collection_path}")
    except Exception as e:
        print(f"Lỗi khi tạo hoặc lưu DB: {e}")
        return None
    return db

create_db_from_files()
