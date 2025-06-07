import torch
import os
import uuid
from gtts import gTTS
from flask import Flask, request, jsonify, send_from_directory
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant, FAISS
from qdrant_client import QdrantClient
from langchain.llms.base import LLM
from llama_cpp import Llama
from typing import Optional, List, Any
import random
import string
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# Khai bao bien
app = Flask(__name__)
data_path = "dataset"
number_get = 2
AUDIO_FOLDER = "audio"

model_GGUF = "models/vinallama-7b-chat_q5_0.gguf"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"  # Mô hình nhúng câu từ HuggingFace

general_temperature = 0.01
datapath = "vector_store"
collection_path = "collection"
max_token = 260

class LlamaCppWrapper(LLM):
    llama: Any = None
    
    def __init__(self, model_path: str, **kwargs):
        super().__init__()
        # Cấu hình tối ưu cho RTX 3050
        self.llama = Llama(
            model_path=model_path,
            n_gpu_layers=32,    # Số lớp GPU, điều chỉnh theo GPU của bạn
            n_ctx=4096,
            n_batch=512,
            n_threads=6,
            verbose=True,
            
            use_mmap=True,
            use_mlock=True,
            
            f16_kv=True,
            **kwargs
        )
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        response = self.llama(
            prompt,
            max_tokens=max_token,
            temperature=general_temperature,
            top_p=0.9,
            stop=stop or [],
            echo=False
        )
        return response['choices'][0]['text']
    
    @property
    def _llm_type(self) -> str:
        return "llama-cpp"
    
def read_vectors_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )
    print(f"Đang tải vector database từ: {datapath}, collection: {collection_path}")
    if not os.path.exists(datapath):
        print(f"LỖI: Đường dẫn lưu trữ {datapath} không tồn tại.")
        return None

    client = QdrantClient(path=datapath)

    try:
        collection_info = client.get_collection(collection_name=collection_path)
        if collection_info.points_count == 0:
            print(f"CẢNH BÁO: Collection Qdrant '{collection_path}' trống.")
    except Exception as e:
        print(f"LỖI: Không thể lấy thông tin collection '{collection_path}'. Nó có thể chưa được tạo. Lỗi: {e}")
        print("Hãy chắc chắn rằng bạn đã chạy 'prepare_vector_db.py' để tạo và điền dữ liệu vào collection.")
        return None

    db = Qdrant(
        client=client,
        collection_name=collection_path,
        embeddings=embedding_model
    )
    print("Đã kết nối tới vector database.")
    return db

def load_llm(model_gguf_path):
    if not os.path.exists(model_gguf_path):
        print(f"LỖI: Không tìm thấy tệp model GGUF tại {model_gguf_path}")
        return None

    print("Đang tải model")
    try:
        llm = LlamaCppWrapper(model_path=model_gguf_path)
        print("Model đã được tải thành công")
        return llm
    except Exception as e:
        print(f"Lỗi khi tải model: {e}")
        return None

def create_prompt(template_model):
    prompt = PromptTemplate(template=template_model, input_variables=["context", "question"])
    return prompt

def create_qa_chain(prompt, llm, db):
    Retriever = db.as_retriever(search_kwargs={"k": number_get}) # number_get chỉ là một con số (số doc cần lấy)    
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=Retriever,
        return_source_documents=True, # Đặt thành True nếu bạn muốn xem tài liệu nào đã được truy xuất (hữu ích khi debug)
        chain_type_kwargs={'prompt': prompt}
    )
    return chain

def generate_audio_filename():
    # Sinh tên file 4 ký tự gồm chữ cái in hoa và số
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + ".mp3"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("question", "").strip()
        print(f" Đã nhận câu hỏi: {question}")
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

        template ="""<|im_start|>system\n
            Bạn là một trợ lý tư vấn tuyển sinh. Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, chỉ cần trả lời những câu lịch sự như "Tôi thực sự xin lỗi, tôi không thể trả lời câu hỏi của bạn". Bạn đừng cố bịa ra câu trả lời, cũng đừng hallucinate. Trả lời câu hỏi dưới đây:\n
            {context}<|im_end|>\n
            <|im_start|>user\n
            {question}<|im_end|>\n
            <|im_start|>assistant"""
        
        print("Tạo prompt từ template...")
        prompt = create_prompt(template)

        print("Tạo chuỗi LLM với truy xuất RAG...")
        llm_chain = create_qa_chain(prompt, llm, db)

        print("Bắt đầu trả lời câu hỏi...")
        answer = llm_chain.invoke({"query": question})
        # Tạo audio sẵn
        filename = generate_audio_filename()
        path = os.path.join(AUDIO_FOLDER, filename)
        tts = gTTS(text=answer['result'], lang="vi")
        tts.save(path)
        audio_url = f"/audio/{filename}"

        print("Trả kết quả về frontend...")
        print(f"Kết quả từ LLM: {answer}")
        if 'result' not in answer:
            return jsonify({"answer": {"result": "Lỗi: Không tìm thấy 'result' trong phản hồi của LLM.", "audio_url": None}}), 200

        return jsonify({"answer": {"result": answer.get("result", ""), "audio_url": audio_url}}), 200
    
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi xử lý câu hỏi: {str(e)}")
        import traceback
        traceback.print_exc() # In traceback đầy đủ để debug
        return jsonify({"error": f"Lỗi xử lý nghiêm trọng: {str(e)}"}), 500

@app.route("/tts", methods=["POST"])
def tts():
    text = request.json.get("text", "").strip()
    if not text:
        return jsonify({"Lỗi": "Không có text nào được cung cấp"}), 400

    try:
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join(AUDIO_FOLDER, filename)
        tts = gTTS(text=text, lang="vi")
        tts.save(path)
        return jsonify({"audio_url": f"/audio/{filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_FOLDER, filename)

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
    app.run(host='0.0.0.0', port=5000, debug=True)