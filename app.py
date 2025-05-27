from flask import Flask, request, jsonify, send_from_directory
from openai import OpenAI
import os
from search_engine import search_best_chunk_with_embedding
import random
app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DEFAULT_RESPONSES = [
    "Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM và sẵn sàng hỗ trợ bạn về thông tin tuyển sinh và các vấn đề liên quan đến trường. Nếu bạn có câu hỏi nào về trường, ngành học, điểm chuẩn hay thông tin tuyển sinh, hãy cho tôi biết!",
    "Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM và không có thông tin về cá nhân cụ thể nào. Nếu bạn có câu hỏi nào liên quan đến trường, ngành học, điểm chuẩn hay thông tin tuyển sinh, hãy cho tôi biết!"
]
@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question")
    print(">>> Nhận câu hỏi:", question)
    if not question:
        return jsonify({"error": "Câu hỏi không được để trống."}), 400
    # 1. Lấy context bằng embedding
    context = search_best_chunk_with_embedding(question)
    print(">>> Context gửi vào GPT:\n", context)
    if not context:
        return jsonify({"answer": random.choice(DEFAULT_RESPONSES)})

    # 2. Gửi vào ChatGPT
    messages = [
        {"role": "system", "content": f"Bạn là trợ lý tuyển sinh. Trả lời NGẮN GỌN, CỤ THỂ chỉ dựa trên thông tin sau:\n\n{context}"},
        {"role": "user", "content": question}
    ]
    chat_resp = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3,
        max_tokens=300
    )
    answer = chat_resp.choices[0].message.content
    print(">>> GPT Response:\n", chat_resp)
    return jsonify({"answer": answer})

# Phần serve UI...
@app.route("/")
def serve_ui():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def serve_css():
    return send_from_directory(".", "style.css")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
