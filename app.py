from flask import Flask, request, jsonify, send_from_directory
import openai
from chat_engine import load_chunks, build_vectorizer, search_best_chunk
import os

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

chunks = load_chunks("data.txt")
vectorizer, vectors = build_vectorizer(chunks)

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question")
    context = search_best_chunk(question, vectorizer, vectors, chunks)
    if not context:
        return jsonify({"answer": "Xin lỗi, tôi chưa có thông tin phù hợp để trả lời câu hỏi này."})

    messages = [
        {"role": "system", "content": f"Trả lời ngắn gọn và cụ thể dựa trên thông tin sau:\n\n{context}"},
        {"role": "user", "content": question}
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3,
        max_tokens=300
    )
    answer = response.choices[0].message["content"]
    return jsonify({"answer": answer})

# 👇 PHẦN GIAO DIỆN WEB TẠI ĐÂY
@app.route("/")
def serve_ui():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def serve_css():
    return send_from_directory(".", "style.css")

# if __name__ == "__main__":
#     port = int(os.environ.get("PORT", 5000))
#     app.run(host="0.0.0.0", port=port)
