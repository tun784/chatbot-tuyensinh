# search_engine.py
import google.generativeai as genai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Cấu hình Google GenAI ---
# Đảm bảo biến môi trường GOOGLE_API_KEY đã được đặt
# Bạn có thể đặt nó trong run.sh hoặc trực tiếp trong môi trường của bạn
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Lỗi: Vui lòng đặt biến môi trường GOOGLE_API_KEY.")
    exit()
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Lỗi cấu hình Google GenAI: {e}")
    exit()

# --- Tải Chunks và Embeddings ---
def load_chunks_and_embeddings(path="chunks_with_embeddings.json"):
    """Tải dữ liệu chunks và embeddings từ file JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Đã tải thành công {len(data)} chunks từ {path}")
        return data
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {path}. Hãy chắc chắn bạn đã chạy build_embeddings.py.")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi: File {path} không chứa JSON hợp lệ.")
        return []
    except Exception as e:
        print(f"Lỗi không xác định khi tải {path}: {e}")
        return []

chunks_data = load_chunks_and_embeddings()
if chunks_data:
    # Tạo ma trận embeddings để tính toán hiệu quả
    embeddings_matrix = np.array([item["embedding"] for item in chunks_data])
else:
    embeddings_matrix = np.array([])

# --- Tạo Embedding cho Câu hỏi ---
def get_question_embedding(question):
    """Tạo embedding cho câu hỏi sử dụng model của Google."""
    try:
        resp = genai.embed_content(
            model="models/text-embedding-004", # Cùng model với lúc build
            content=question,
            task_type="retrieval_query" # Quan trọng: Dùng 'retrieval_query' cho câu hỏi
        )
        return resp['embedding']
    except Exception as e:
        print(f"Lỗi khi tạo embedding cho câu hỏi '{question}': {e}")
        return None

# --- Tìm kiếm Chunk Tốt nhất ---
def search_best_chunk_with_embedding(question, threshold=0.7):
    """Tìm kiếm chunk văn bản có độ tương đồng cosine cao nhất với câu hỏi."""
    if not chunks_data or embeddings_matrix.size == 0:
        print("Lỗi: Dữ liệu chunks hoặc embeddings chưa được tải.")
        return None

    question_embedding = get_question_embedding(question)
    if question_embedding is None:
        return None # Không thể tạo embedding cho câu hỏi

    # Tính độ tương đồng Cosine
    sims = cosine_similarity([question_embedding], embeddings_matrix)[0]

    # Tìm chỉ số và giá trị tương đồng cao nhất
    idx = int(np.argmax(sims))
    max_sim = sims[idx]
    # --- Thêm các dòng print sau đây để gỡ lỗi ---
    print(f"------------------------------------------------------------------------------")
    print(f"Câu hỏi: {question}")
    print(f"Độ tương đồng cao nhất tìm được: {sims[idx]:.4f}")
    print(f"Chunk được chọn (index {idx}):")
    print(chunks[idx])
    print(f"-------------------------------------------------------------------------------")
    # ---------------------------------------------

    print(f">>> Độ tương đồng cao nhất: {max_sim:.4f} tại chunk {idx} ({chunks_data[idx]['filename']})")

    # Chỉ trả về context nếu độ tương đồng đạt ngưỡng
    if max_sim >= threshold:
        print(f">>> Tìm thấy chunk phù hợp (Ngưỡng {threshold}).")
        return chunks_data[idx]["text"]
    else:
        print(f">>> Độ tương đồng ({max_sim:.4f}) dưới ngưỡng ({threshold}). Không trả về context.")
        # Bạn có thể cân nhắc trả về chunk gần nhất dù dưới ngưỡng
        # return chunks_data[idx]["text"]
        return None
    
