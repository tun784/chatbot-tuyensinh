# chat_api.py
# Gửi prompt + ngữ cảnh vào GPT-3.5 để tạo câu trả lời

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_answer_from_gpt(question, context):
    messages = [
        {"role": "system", "content": f"Trả lời ngắn gọn và cụ thể dựa trên thông tin sau:\n\n{context}"},
        {"role": "user", "content": question}
    ]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.3,
        max_tokens=300
    )
    return response.choices[0].message.content
