import google.generativeai as genai
import os

# Đảm bảo GOOGLE_API_KEY đã được đặt trong biến môi trường
# Nếu chưa, hãy đặt như đã hướng dẫn trước đó:
# set GOOGLE_API_KEY=your_google_api_key_here (cmd)
# $env:GOOGLE_API_KEY="your_google_api_key_here" (powershell)
genai.configure(api_key=os.getenv("AIzaSyDl65_4Px2JI0onfSZzp7k74LUfqNCbDWc"))

print("Các mô hình Google Generative AI khả dụng với API Key của bạn:")
for m in genai.list_models():
  print(f"  Tên model: {m.name}")
  print(f"    Phương thức hỗ trợ: {m.supported_generation_methods}")
  print("-" * 30)

# Sau khi chạy xong, hãy xóa hoặc comment đoạn code này trước khi chạy app.py chính thức