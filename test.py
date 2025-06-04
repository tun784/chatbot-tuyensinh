import torch
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L12-v2",
    model_kwargs={"device": "cuda"}
)

print(f"CUDA Available on Kaggle: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
    
    # Kiểm tra VRAM (ví dụ, không phải là cách chính xác nhất nhưng cho ý tưởng)
    # t = torch.cuda.get_device_properties(0)
    # print(f"Total VRAM: {t.total_memory / (1024**3):.2f} GB")

print(f"Embedding model device: {embedding_model.client.device}")