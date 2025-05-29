# search_engine.py (Phiên bản Debug - Luôn trả về context)
import google.generativeai as genai
import os
import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# --- Cấu hình Google GenAI ---
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Lỗi: Vui lòng đặt biến môi trường GOOGLE_API_KEY.")
    # exit() 
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Lỗi cấu hình Google GenAI: {e}")

# --- Tải Chunks và Embeddings ---
def load_chunks_and_embeddings(path="chunks_with_embeddings.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Đã tải thành công {len(data)} chunks từ {path}")
        return data
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {path}.")
        return []
    except json.JSONDecodeError:
        print(f"Lỗi: File {path} không chứa JSON hợp lệ.")
        return []
    except Exception as e:
        print(f"Lỗi không xác định khi tải {path}: {e}")
        return []

chunks_data = load_chunks_and_embeddings()
embeddings_matrix = np.array([])
if chunks_data:
    try:
        # Kiểm tra xem tất cả các item có 'embedding' không
        valid_items = [item for item in chunks_data if "embedding" in item and isinstance(item["embedding"], list)]
        if len(valid_items) < len(chunks_data):
            print(f"Cảnh báo: {len(chunks_data) - len(valid_items)} chunks thiếu trường 'embedding' hoặc embedding không phải list.")
        if valid_items: # Chỉ tạo matrix nếu có item hợp lệ
            embeddings_matrix = np.array([item["embedding"] for item in valid_items])
        else:
            print("Lỗi: Không có chunk nào có embedding hợp lệ.")
    except Exception as e: # Bắt lỗi chung khi tạo matrix
        print(f"Lỗi khi tạo embedding matrix: {e}")
        embeddings_matrix = np.array([])
else:
    print("Thông báo: Không có dữ liệu chunks nào được tải, embeddings_matrix sẽ rỗng.")

# --- Tạo Embedding cho Câu hỏi ---
def get_question_embedding(question):
    print(f">>> Đang tạo embedding cho: '{question}'")
    if not API_KEY:
        print("!!! LỖI: GOOGLE_API_KEY chưa được đặt.")
        return None
    if genai.get_model('models/text-embedding-004') is None: # Kiểm tra model tồn tại
        print("!!! LỖI: Model 'models/text-embedding-004' không khả dụng.")
        return None
    try:
        resp = genai.embed_content(
            model="models/text-embedding-004",
            content=question,
            task_type="retrieval_query"
        )
        print(f">>> Tạo embedding thành công.")
        return resp['embedding']
    except Exception as e:
        print(f"!!! LỖI embedding: {e}")
        return None

# --- Tìm kiếm Chunk Tốt nhất ---
def search_best_chunk_with_embedding(question): # Bỏ threshold ở đây
    if not chunks_data or embeddings_matrix.size == 0: # Kiểm tra cả hai
        print("Lỗi: Dữ liệu chunks hoặc embeddings chưa được tải hoặc rỗng trong search_best_chunk_with_embedding.")
        return None
        
    question_embedding = get_question_embedding(question)
    if question_embedding is None:
        return None

    try:
        sims = cosine_similarity([question_embedding], embeddings_matrix)[0]
    except ValueError as e:
        print(f"!!! LỖI khi tính cosine_similarity: {e}")
        print(f"Shape của question_embedding: {np.array(question_embedding).shape}")
        print(f"Shape của embeddings_matrix: {embeddings_matrix.shape}")
        return None
    idx = int(np.argmax(sims))
    max_sim = sims[idx]

    # Log bạn đã thêm vào
    print("------------------------------------------------------------------------------")
    print(f"Câu hỏi: {question}")
    print(f"Độ tương đồng cao nhất tìm được: {max_sim:.4f}") 
    print(f"Chunk được chọn (index {idx}):")
    # Sử dụng json.dumps để in dict đẹp hơn, tránh lỗi nếu có ký tự đặc biệt
    try:
        print(json.dumps(chunks_data[idx], ensure_ascii=False, indent=2))
    except IndexError:
        print(f"Lỗi: Không thể truy cập chunks_data tại index {idx}. Số lượng chunks: {len(chunks_data)}")
        return None # Hoặc xử lý lỗi khác
    print("-------------------------------------------------------------------------------")

    print(f">>> Độ tương đồng cao nhất: {max_sim:.4f} tại chunk {idx} ({chunks_data[idx]['filename']})")
    
    # LUÔN TRẢ VỀ CHUNK TỐT NHẤT ĐỂ DEBUG
    print(f">>> (DEBUG) Luôn trả về chunk: {chunks_data[idx]['filename']}")
    # In ra một phần context để xem nó là gì
    context_to_send = chunks_data[idx]["text"]
    print(f">>> (DEBUG) Một phần context sẽ gửi cho AI: {context_to_send[:500]}...") 
    return context_to_send