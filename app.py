import torch
import os
import uuid
from gtts import gTTS
from flask import Flask, request, jsonify, send_from_directory
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Qdrant
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
number_get = 2
AUDIO_FOLDER = "audio"
model = "models/vinallama-7b-chat-Q8_0.gguf"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"

general_temperature = 0.01
qdrant_persistent_path = "vector_store"
collection_path = "admissions_info"
max_token = 365

class LlamaCppWrapper(LLM):
    llama: Any = None
    
    def __init__(self, model_path: str, **kwargs):
        super().__init__()
        self.llama = Llama(
            model_path=model_path,
            n_gpu_layers=32,    # Số lớp GPU
            n_ctx=4096, # Kích thước ngữ cảnh
            n_batch=512, # Kích thước batch
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
    
# Khởi tạo database và model LLM toàn cục khi app khởi động
print("Đang khởi tạo vector database...")
global_db = None
global_llm = None
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )
    client = QdrantClient(path=qdrant_persistent_path)
    global_db = Qdrant(
        client=client,
        collection_name=collection_path,
        embeddings=embedding_model
    )
    print("Đã khởi tạo vector database thành công.")
except Exception as e:
    print(f"LỖI khi khởi tạo vector database: {e}")

print("Đang khởi tạo model LLM...")
global_llm = None
try:
    if not os.path.exists(model):
        print(f"LỖI: Không tìm thấy tệp model GGUF tại {model}")
    else:
        global_llm = LlamaCppWrapper(model_path=model)
        print("Đã khởi tạo model LLM thành công.")
except Exception as e:
    print(f"LỖI khi khởi tạo model LLM: {e}")

def read_vectors_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"}
    )
    print(f"Đang tải vector database từ collection: {collection_path}")
    client = QdrantClient(path=qdrant_persistent_path)
    try:
        collection_info = client.get_collection(collection_name=collection_path)
        if collection_info.points_count == 0:
            print(f"CẢNH BÁO: Collection Qdrant '{collection_path}' trống.")
    except Exception as e:
        print(f"LỖI: Không thể lấy thông tin collection '{collection_path}'. Lỗi: {e}")
        return None
    db = Qdrant(
        client=client,
        collection_name=collection_path,
        embeddings=embedding_model
    )
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
        return_source_documents=True, # Đặt thành True để xem tài liệu nào đã được truy xuất
        chain_type_kwargs={'prompt': prompt}
    )
    return chain

def generate_audio_filename():
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choices(chars, k=4)) + ".mp3"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        question = request.json.get("question", "").strip()
        print(f" Đã nhận câu hỏi: {question}")
        if not question:
            return jsonify({"error": "Câu hỏi không được để trống."}), 400
        # Sử dụng lại database và model đã khởi tạo
        db = global_db
        llm = global_llm
        if db is None:
            print("Không tìm thấy vector database.")
            return jsonify({"error": "Không tìm thấy vector database"}), 500
        if llm is None:
            return jsonify({"error": "Không thể tải mô hình LLM. Kiểm tra đường dẫn và cấu hình."}), 500
        print("Kiểm tra truy xuất context từ câu hỏi")
        docs = db.similarity_search(question, k=number_get)
        for i, doc in enumerate(docs):
            print(f"\n--- Kết quả {i+1} ---\n{doc.page_content}\n")
        print("----------------------------------------------------------------")
        template ="""<|im_start|>system\n
            Bạn là một trợ lý tư vấn tuyển sinh của Trường Đại học Công Thương Thành phố Hồ Chí Minh, bạn đang tư vấn tuyển sinh cho học sinh và phụ huynh. 
            Bạn sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, chỉ cần trả lời những câu lịch sự như "Tôi thực sự xin lỗi, tôi không thể trả lời câu hỏi của bạn". 
            Bạn đừng cố bịa ra câu trả lời, cũng đừng hallucinate. Trả lời câu hỏi dưới đây:\n
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
        traceback.print_exc()
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
@app.route('/img/<path:filename>')
def serve_img(filename):
    return send_from_directory('frontend/img', filename)
@app.route('/styles/<path:filename>')
def serve_css(filename):
    return send_from_directory('frontend/styles', filename)
@app.route('/scripts/<path:filename>')
def serve_js(filename):
    return send_from_directory('frontend/scripts', filename)
@app.route('/')
def serve_ui():
    return send_from_directory('frontend', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)