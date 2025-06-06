import torch
from langchain_huggingface import HuggingFaceEmbeddings
import os
from langchain_community.llms import LlamaCpp
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

print(f"CUDA Available on PC: {torch.cuda.is_available()}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Device count: {torch.cuda.device_count()}")
    print(f"Current device: {torch.cuda.current_device()}")
    print(f"Device name: {torch.cuda.get_device_name(torch.cuda.current_device())}")
    # Kiểm tra VRAM (ví dụ, không phải là cách chính xác nhất nhưng cho ý tưởng)
    t = torch.cuda.get_device_properties(0)
    print(f"Total VRAM: {t.total_memory / (1024**3):.2f} GB")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L12-v2",
    model_kwargs={"device": "cuda"}
)

print(f"Embedding model device: {embedding_model.client.device}")