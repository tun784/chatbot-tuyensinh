from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
from qdrant_client import QdrantClient
import torch
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Khai bao bien
app = Flask(__name__)
data_path = "dataset"
number_get = 4  # Số lượng kết quả trả về từ FAISS

model_vinallama = "models/vinallama-7b-chat_q5_0.gguf"
model_GGUF = model_vinallama  # Chọn mô hình LLM, có thể là vinallama hoặc phogpt
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"  # Mô hình nhúng câu từ HuggingFace

general_temperature = 0.01
qdrant_persistent_path = "qdrant_vector_store" # Thư mục Qdrant lưu trữ dữ liệu
qdrant_collection_name = "admissions_collection"
max_token = 512

def read_vectors_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}  # Chạy bằng RTX 3050
    )
    print(f"Đang tải vector database từ: {qdrant_persistent_path}, collection: {qdrant_collection_name}")
    if not os.path.exists(qdrant_persistent_path):
        print(f"LỖI: Đường dẫn lưu trữ {qdrant_persistent_path} không tồn tại. Hãy chạy prepare_vector_db.py trước.")
        return None # Hoặc raise Exception

    client = QdrantClient(path=qdrant_persistent_path)

    # Kiểm tra xem collection có tồn tại không
    try:
        collection_info = client.get_collection(collection_name=qdrant_collection_name)
        print(f"Thông tin collection Qdrant: {collection_info}")
        if collection_info.points_count == 0:
            print(f"CẢNH BÁO: Collection Qdrant '{qdrant_collection_name}' trống. Hãy đảm bảo prepare_vector_db.py đã chạy thành công và có dữ liệu.")
    except Exception as e: # Exception có thể là qdrant_client.http.exceptions.UnexpectedResponse
        print(f"LỖI: Không thể lấy thông tin collection '{qdrant_collection_name}'. Nó có thể chưa được tạo. Lỗi: {e}")
        print("Hãy chắc chắn rằng bạn đã chạy 'prepare_vector_db.py' để tạo và điền dữ liệu vào collection.")
        return None


    db = Qdrant(
        client=client,
        collection_name=qdrant_collection_name,
        embeddings=embedding_model # Langchain Qdrant wrapper cần embeddings để hoạt động như một retriever
    )
    print("Đã kết nối tới vector database.")
    return db

def load_llm(model_gguf_path):
    if not os.path.exists(model_gguf_path):
        print(f"LỖI: Không tìm thấy tệp model GGUF tại {model_gguf_path}")
        return None

    llm = LlamaCpp(
        model_path=model_gguf_path,
        n_gpu_layers=5, # Điều chỉnh giá trị này dựa trên VRAM RTX 3050 của bạn
        n_ctx=4096,       # Số lượng token tối đa trong ngữ cảnh của LLM
        n_batch=512,      # Kích thước batch xử lý token, có thể cần điều chỉnh dựa trên VRAM
        max_tokens=max_token, # Số token tối đa mà LLM sẽ tạo ra cho một câu trả lời
        temperature=general_temperature,
        top_p=0.9,
        use_mlock=True,   # Giúp giữ model trong RAM (nếu đủ RAM hệ thống)
        use_mmap=True,    # Sử dụng memory mapping, có thể cải thiện tốc độ tải model
        f16_kv=True,     # THAY ĐỔI: Sử dụng FP32 cho key/value cache. Sẽ tốn nhiều VRAM hơn.
        verbose=True     # Đặt thành True để xem output chi tiết từ llama.cpp khi khởi tạo/suy luận
    )
    return llm

def create_prompt(template):
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    return prompt

def create_qa_chain(prompt, llm, db):
    # db ở đây là instance của Qdrant vector store
    retriever = db.as_retriever(search_kwargs={"k": number_get}) # number_get chỉ là một con số (số doc cần lấy)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff", # "stuff" phù hợp cho context ngắn, nếu context dài có thể cân nhắc "map_reduce" hoặc "refine"
        retriever=retriever,
        return_source_documents=False, # Đặt thành True nếu bạn muốn xem tài liệu nào đã được truy xuất (hữu ích khi debug)
        chain_type_kwargs={'prompt': prompt}
    )
    return chain

@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("question", "").strip()
        print(f">>> Đã nhận câu hỏi: {question}")
        if not question:
            return jsonify({"error": "Câu hỏi không được để trống."}), 400
        
        print("Bắt đầu đọc database...")
        db = read_vectors_db()
        if db is None:
            return jsonify({"Không tìm thấy vector database"}), 500
        print("Đã tải thành công vector database.")

        print("Kiểm tra truy xuất context từ câu hỏi")
        docs = db.similarity_search(question, k=number_get)
        for i, doc in enumerate(docs):
            print(f"\n--- Kết quả {i+1} ---\n{doc.page_content}\n")

        print("Tải mô hình LLM...")
        llm = load_llm(model_GGUF)
        if llm is None:
            return jsonify({"error": "Không thể tải mô hình LLM. Kiểm tra đường dẫn và cấu hình."}), 500

        template = """<|im_start|>system\n
            Bạn là một trợ lý tư vấn tuyển sinh. Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy trả lời những câu lịch sự như "Tôi thực sự xin lỗi, tôi không tìm thấy thông tin liên quan trong dữ liệu", đừng cố bịa ra câu trả lời, cũng đừng hallucinate. Trả lời câu hỏi dưới đây:\n
            {context}<|im_end|>\n
            <|im_start|>user\n
            {question}<|im_end|>\n
            <|im_start|>assistant"""

        print("Tạo prompt từ template...")
        prompt = create_prompt(template)

        print("Tạo chuỗi LLM với truy xuất RAG...")
        llm_chain = create_qa_chain(prompt, llm, db)

        print("Bắt đầu trả lời câu hỏi...")
        answer = llm_chain.invoke({"query": question}) # answer là một dictionary
        
        print("Trả kết quả về frontend...")
        print(f"Kết quả từ LLM: {answer}") # Nên là {'query': '...', 'result': '...'}
                                            # Nếu return_source_documents=True, sẽ có thêm 'source_documents'
        
        # script.js mong đợi dataset.answer.result, vì vậy chúng ta cần đảm bảo 'answer' trong JSON response chứa 'result'
        # Nếu llm_chain.invoke trả về một dict có key 'result', thì answer['result'] là câu trả lời.
        # Nếu cấu trúc khác, bạn cần điều chỉnh ở đây hoặc trong script.js
        if 'result' not in answer:
            print(f"CẢNH BÁO: Key 'result' không có trong dictionary trả về từ llm_chain.invoke. Dictionary: {answer}")
            # Gửi toàn bộ dict nếu 'result' không có, hoặc một thông báo lỗi cụ thể hơn
            return jsonify({"answer": {"result": "Lỗi: Không tìm thấy 'result' trong phản hồi của LLM."}}), 200

        return jsonify({"answer": answer}), 200
    
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi xử lý câu hỏi: {str(e)}")
        import traceback
        traceback.print_exc() # In traceback đầy đủ để debug
        return jsonify({"error": f"Lỗi xử lý nghiêm trọng: {str(e)}"}), 500

# Phần serve UI...
@app.route("/")
def serve_ui():
    return send_from_directory(".", "index.html")

@app.route("/styles/style.css")
def serve_css():
    return send_from_directory("styles", "style.css")

@app.route("/scripts/script.js")
def serve_js():
    return send_from_directory("scripts", "script.js")

@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('img', filename)

if __name__ == '__main__':
    # Đảm bảo thư mục 'qdrant_vector_store' và collection tồn tại trước khi chạy.
    # Bạn thường chạy prepare_vector_db.py một lần để tạo nó.

    if not os.path.exists(qdrant_persistent_path):
        print(f"CẢNH BÁO: Đường dẫn Qdrant {qdrant_persistent_path} không tồn tại. Hãy đảm bảo chạy prepare_vector_db.py trước.")
    else:
        # Kiểm tra nhanh xem collection có dữ liệu không (tùy chọn)
        try:
            client_check = QdrantClient(path=qdrant_persistent_path)
            collection_info_check = client_check.get_collection(collection_name=qdrant_collection_name)
            if collection_info_check.points_count == 0:
                 print(f"CẢNH BÁO KHI KHỞI ĐỘNG APP: Collection Qdrant '{qdrant_collection_name}' tại '{qdrant_persistent_path}' đang trống.")
            else:
                 print(f"Collection Qdrant '{qdrant_collection_name}' có {collection_info_check.points_count} điểm dữ liệu.")
            client_check.close()
        except Exception as e:
            print(f"CẢNH BÁO KHI KHỞI ĐỘNG APP: Không thể kiểm tra collection Qdrant '{qdrant_collection_name}'. Lỗi: {e}")
            print("Hãy chắc chắn rằng bạn đã chạy 'prepare_vector_db.py' thành công.")

    app.run(host='0.0.0.0', port=5000, debug=False)