from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import os
from search_engine import search_best_chunk_with_embedding # Đảm bảo import từ file mới
import random

app = Flask(__name__)
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("Lỗi: Vui lòng đặt biến môi trường GOOGLE_API_KEY.")
    exit()
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Lỗi cấu hình Google GenAI: {e}")
    exit()

DEFAULT_RESPONSES = [
    "Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM và sẵn sàng hỗ trợ bạn về thông tin tuyển sinh và các vấn đề liên quan đến trường. Nếu bạn có câu hỏi nào về trường, ngành học, điểm chuẩn hay thông tin tuyển sinh, hãy cho tôi biết!",
    "Xin chào! Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM. Bạn cần thông tin gì về tuyển sinh hay các ngành học của trường?",
    "Chào bạn! Tôi là trợ lý tư vấn của trường Đại học Công Thương TPHCM. Nếu bạn có câu hỏi về tuyển sinh, điểm chuẩn hay các ngành học, hãy cho tôi biết nhé!",
]

@app.route("/chat", methods=["POST"])
def chat():
    question = request.json.get("question")
    print(f">>> Nhận câu hỏi: {question}")
    if not question:
        return jsonify({"error": "Câu hỏi không được để trống."}), 400

    # 1. Lấy context bằng embedding
    context = search_best_chunk_with_embedding(question)
    print(f">>> Context gửi vào Google GenAI:\n{context if context else '<<Không tìm thấy context phù hợp>>'}")
    if not context:
        return jsonify({"answer": random.choice(DEFAULT_RESPONSES)})

    # 2. Gửi vào Google Generative AI
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        prompt = f"""Bạn là một trợ lý ảo tư vấn tuyển sinh cho Trường Đại học Công Thương TP.HCM (HUIT). Nhiệm vụ của bạn là trả lời các câu hỏi của sinh viên và phụ huynh một cách thân thiện, chính xác và **CHỈ DỰA VÀO NỘI DUNG ĐƯỢC CUNG CẤP** dưới đây.
        Nếu câu hỏi không liên quan đến HUIT hoặc không thể trả lời dựa trên nội dung, hãy trả lời một cách lịch sự rằng bạn chưa có thông tin đó hoặc hỏi lại câu hỏi khác.
        Tuyệt đối không tự bịa thông tin. Trả lời ngắn gọn, tập trung vào câu hỏi.

        Nội dung tham khảo (Context):
        ---
        {context}
        ---

        Câu hỏi của người dùng: {question}

        Câu trả lời của bạn:"""

        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        chat_resp = model.generate_content(prompt, safety_settings=safety_settings)

        if chat_resp.parts:
            answer = chat_resp.text
        else:
            answer = "Rất tiếc, tôi không thể trả lời câu hỏi này vào lúc này. Vui lòng thử lại sau."
            print(">>> Google GenAI Response bị chặn hoặc rỗng.")

        print(f">>> Google GenAI Response:\n{chat_resp}") #debug
        return jsonify({"answer": answer})

    except Exception as e:
        print(f">>> Lỗi khi gọi Google GenAI: {e}")
        return jsonify({"answer": random.choice(DEFAULT_RESPONSES)})

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