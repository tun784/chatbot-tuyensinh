from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader, PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import LlamaCpp
import torch
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Khai bao bien
data_path = "data"
vector_db_path = "vectordatabase/db_faiss"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"
size = 200  # Kích thước chunk cho text splitter
overlap = 40  # Số ký tự chồng lắp giữa các chunk

def create_db_from_files():
    if not os.path.exists(data_path):
        print(f"Thư mục {data_path} không tồn tại. Vui lòng tạo thư mục và thêm dữ liệu.")
        return
    
    print("Bắt đầu tạo vector store từ các file trong thư mục data")
    loader = DirectoryLoader(
        data_path,
        glob="*.txt",
        loader_cls=lambda path: TextLoader(path, encoding="utf-8")
    )

    print("Đang tải dữ liệu từ các file...")
    documents = loader.load()
    if not documents:
        print("Không có tài liệu nào được tải. Vui lòng kiểm tra lại thư mục data.")
        return
    else:
        print(f"Đã tải {len(documents)} tài liệu từ thư mục {data_path}.")

    print("Đang chia nhỏ tài liệu thành các đoạn...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    print("Sử dụng RecursiveCharacterTextSplitter để chia nhỏ tài liệu...")
    chunks = text_splitter.split_documents(documents)
    print("Đã chia nhỏ tài liệu thành các đoạn:")
    # for i, chunk in enumerate(chunks):
    #     print(f"Đoạn {i+1}: {chunk.page_content[:50]}...")  # Hiển thị 50 ký tự đầu tiên của mỗi đoạn
    print(f"Tổng số đoạn đã chia: {len(chunks)}")

    print(f"Sử dụng mô hình nhúng: {model_sentence}")
    print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else "Không có GPU nào" + "được sử dụng.")

    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda"}  # Chạy bằng RTX 3050
    )
    
    print("Đang tạo vector store...")
    db = FAISS.from_documents(chunks, embedding_model)
    print("Đã tạo vector store thành công.")
    db.save_local(vector_db_path)
    print(f"Vector store được lưu vào {vector_db_path}")
    return db

create_db_from_files()
