from flask import Flask, request, jsonify, send_from_directory
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQAWithSourcesChain, RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader, TextLoader
import torch
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Khai bao bien
app = Flask(__name__)
data_path = "data"

# model_PhoGPT = AutoModelForCausalLM.from_pretrained("vinai/PhoGPT-4B-Chat").to("cuda")
# model_vinallama = AutoModelForCausalLM.from_pretrained("vilm/vinallama-7b-chat").to("cuda")
# tokenizer = AutoTokenizer.from_pretrained(model_name)
model_vinallama = "models/vinallama-7b-chat_q5_0.gguf"
model_sentence = "sentence-transformers/all-MiniLM-L12-v2"  # Mô hình nhúng câu từ HuggingFace
general_temperature = 0.01
vector_db_path = "vectordatabase/db_faiss"
size = 200  # Kích thước chunk cho text splitter
overlap = 40  # Số ký tự chồng lắp giữa các chunk

def read_vectors_db():
    embedding_model = HuggingFaceEmbeddings(
        model_name=model_sentence,
        model_kwargs={"device": "cuda"}  # Chạy bằng RTX 3050
    )
    print("Đang tải vector database... ", vector_db_path)
    db = FAISS.load_local(vector_db_path, embedding_model, allow_dangerous_deserialization=True)
    return db

def load_llm(model_vinallama):
    llm = LlamaCpp(
        model_path=model_vinallama,
        n_gpu_layers=64,  # Số layer chạy trên GPU, tùy VRAM
        n_ctx=4096,  # Số lượng token tối đa trong ngữ cảnh
        n_batch=512,  # Kích thước batch
        max_tokens=1024,
        temperature=general_temperature,
        top_p=0.9,
        use_mlock=True,
        use_mmap=True,
        f16_kv=True,
        verbose=False
    )
    return llm

def create_prompt(template):
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    return prompt

def create_qa_chain(prompt, llm, db):
    retriever = db.as_retriever(search_kwargs={"k": 2}, max_tokens_limit=1024)
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=False,
        chain_type_kwargs= {'prompt': prompt}
    )
    return chain

# def generate_answer(context, question):
#     prompt = f"Bạn là một trợ lý tư vấn tuyển sinh. Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu không biết, hãy trả lời lịch sự là không tìm thấy thông tin, đừng cố tạo ra câu trả lời, cũng đừng hallucinate hoặc bịa ra câu trả lời. Trả lời câu hỏi \n{context}\nCâu hỏi: {question}\nTrả lời:"
#     input_ids = tokenizer(prompt, return_tensors="pt").input_ids.cuda()
#     output = model_vinallama.generate(input_ids, max_new_tokens=size, do_sample=True, temperature=general_temperature)
#     answer = tokenizer.decode(output[0], skip_special_tokens=True)
#     return answer.split("Trả lời:")[-1].strip()

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

        print("Tải mô hình LLM...")
        llm = load_llm(model_vinallama)

        template = """<|im_start|>system\n
        Bạn là một trợ lý tư vấn tuyển sinh. Sử dụng thông tin sau đây để trả lời câu hỏi. Nếu bạn không biết câu trả lời, hãy những câu đại loại như "Từ tận đáy lòng, tôi thực sự xin lỗi, tôi không tìm thấy thông tin liên quan trong dữ liệu", đừng cố bịa ra câu trả lời, cũng đừng hallucinate. Trả lời câu hỏi bên dưới\n
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
        
        # # print("Dùng retriever để bắt đầu truy xuất tài liệu liên quan...")
        # # retriever = db.as_retriever(search_kwargs={"k": 2}, max_tokens_limit=1024)
        # # docs = retriever.get_relevant_documents(question)
        # # context = "\n".join([doc.page_content for doc in docs])
        # answer = generate_answer(context, question)

        print("Trả kết quả về frontend...")
        print(answer)
        return jsonify({"answer": answer}), 200
    
    except Exception as e:
        print(f"Lỗi khi xử lý câu hỏi: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    except FileNotFoundError as e:
        print(f"Lỗi: Không tìm thấy tệp hoặc thư mục - {str(e)}")
        return jsonify({"answer": "Xin lỗi, tôi không thể xử lý câu hỏi lúc này. Vui lòng thử lại sau."})

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