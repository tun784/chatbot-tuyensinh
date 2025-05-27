from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import os
from search_engine import search_best_chunk_with_embedding
import random

app = Flask(__name__)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

DEFAULT_RESPONSES = [
    "Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM và sẵn sàng hỗ trợ bạn về thông tin tuyển sinh và các vấn đề liên quan đến trường. Nếu bạn có câu hỏi nào về trường, ngành học, điểm chuẩn hay thông tin tuyển sinh, hãy cho tôi biết!",
    "Xin chào! Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM. Bạn cần thông tin gì về tuyển sinh hay các ngành học của trường?",
    "Chào bạn! Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM. Nếu bạn có câu hỏi về tuyển sinh, điểm chuẩn hay các ngành học, hãy cho tôi biết nhé!",
]

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question")
    print(">>> Nhận câu hỏi:", question)
    if not question:
        return jsonify({"error": "Câu hỏi không được để trống."}), 400

    # 1. Lấy context bằng embedding
    context = search_best_chunk_with_embedding(question)
    print(">>> Context gửi vào Google GenAI:\n", context)
    if not context:
        return jsonify({"answer": random.choice(DEFAULT_RESPONSES)})

    # 2. Gửi vào Google Generative AI
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        prompt = f"Bạn là trợ lý tuyển sinh. Hãy trả lời ngắn gọn CHỈ dựa trên thông tin sau:\n\n{context}\n\nCâu hỏi: {question}"
        # Sử dụng generate_content cho Google Generative AI
        chat_resp = model.generate_content(prompt)
        answer = chat_resp.text
        print(">>> Google GenAI Response:\n", chat_resp)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f">>> Lỗi khi gọi Google GenAI: {e}")
        return jsonify({"answer": random.choice(DEFAULT_RESPONSES)})

# Phần serve UI...
@app.route("/")
def serve_ui():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def serve_css():
    return send_from_directory(".", "style.css")
@app.route("/script.js")
def serve_js():
    return send_from_directory(".", "script.js")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)