import requests
import unicodedata
from bs4 import BeautifulSoup
import re
import os

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def remove_symbols_and_emojis(text):
    
    text = text.replace("🔰", "")
    text = text.replace("🔶", "")
    text = text.replace("🔸", "")
    
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols & More
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002700-\U000027BF"  # Dingbats
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

def clean_text_content(text):
    # Lược bỏ đoạn từ "🔰 Phương thức tuyển sinh:" đến trước "🔰 Tổ hợp xét tuyển:"
    text = re.sub(
        r"Phương thức tuyển sinh:.*?(?=Tổ hợp xét tuyển:)", 
        "", 
        text, 
        flags=re.DOTALL
    )
    text = re.sub(r'\n{2,}', '\n', text)
    # Loại bỏ footer (nếu có)
    # text = re.split(r"---", text, flags=re.IGNORECASE)[0]
    text = re.split(r"5. QUYỀN LỢI CỦA NGƯỜI HỌC", text, flags=re.IGNORECASE)[0]
    # Loại bỏ icon và emoji
    text = remove_symbols_and_emojis(text)
    # Thay thế tab bằng dấu cách
    text = text.replace('\t', ' ').strip()
    return text.strip()

def remove_accents(text):
    """Tạo tên file .txt loại bỏ dấu tiếng Việt."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def slugify(text):
    """Chuyển text thành tên file hợp lệ (slug)."""
    text = remove_accents(text)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text) # Chỉ giữ chữ, số, khoảng trắng, gạch ngang
    text = re.sub(r'\s+', ' ', text) # Thay khoảng trắng bằng _
    text = re.sub(r'\n\n+', '\n', text) # Thay nhiều \n\n bằng 1 \n
    return text.strip()

def crawl_page(url):
    print(f">>> Đang crawl: {url}")
    try:
        response = requests.get(url, headers = headers, timeout=15)
        response.raise_for_status() # Báo lỗi nếu request không thành công
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        title_tag = soup.find("h1", class_="article-title")
        title = title_tag.get_text(strip=True) if title_tag else "unknown_title"

        main_table = soup.find("table", class_="MsoNormalTable")
        
        raw_text = ""
        if main_table:
            print("    -> Tìm thấy MsoNormalTable. Đang lấy text...")
            raw_text = main_table.get_text(strip=False)
        else:
            print("    -> Không thấy MsoNormalTable, thử 'post-body'...")
            post_body = soup.find("div", class_="post-body")
            if post_body:
                raw_text = post_body.get_text(strip=False)
            else:
                print(f"    [!] Không tìm thấy nội dung chính tại: {url}")
                return None # Trả về None nếu không lấy được nội dung

        noidung = clean_text_content(raw_text)

        # Tìm Mã ngành bằng Regex
        ma_nganh = None
        match = re.search(r"MÃ NGÀNH:\s*(\d{7})", noidung, re.IGNORECASE)
        if match:
            ma_nganh = match.group(1)
            print(f"    -> Tìm thấy Mã ngành: {ma_nganh}")
        else:
            print("    -> Không tìm thấy Mã ngành bằng Regex.")
            
        return {            
            # "url": url,
            "ma_nganh": ma_nganh,
            "title": title,
            "noidung": noidung
        }
    
    except requests.exceptions.RequestException as e:
        print(f"[!] Lỗi Request khi crawl {url}: {e}")
        return None
    
    except Exception as e:
        print(f"[!] Lỗi không xác định khi crawl {url}: {e}")
        return None

def crawl_all(urls, output_dir="dataset"):
    """Crawl tất cả URL và lưu vào thư mục 'data'."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for idx, url in enumerate(urls):
        data = crawl_page(url)
        if data and data["noidung"]: # Chỉ lưu nếu có dữ liệu
            filename = f"{slugify(data['title'])}.txt"
            path = os.path.join(output_dir, filename)

            with open(path, "w", encoding="utf-8") as f:
                # f.write(f"URL: {data['url']}\n")
                # f.write(f"Mã ngành: {data['ma_nganh'] if data['ma_nganh'] else 'Không tìm thấy'}\n\n")
                f.write(data["noidung"])

            print(f"     Đã lưu: {filename}")
        else:
            print(f"     Bỏ qua URL (Không có dữ liệu): {url}")
        print("-" * 20) # Thêm dòng phân cách cho dễ nhìn

if __name__ == "__main__":
    danh_sach_url = [
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-thong-tin",
        "https://ts.huit.edu.vn/nganh-dh/nganh-marketing",
        "https://ts.huit.edu.vn/nganh-dh/nganh-ke-toan",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-co-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-tai-chinh-ngan-hang",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-sinh-hoc",
        "https://ts.huit.edu.vn/nganh-dh/nganh-luat-kinh-te",
        "https://ts.huit.edu.vn/nganh-dh/nganh-logistic-va-quan-ly-chuoi-cung-ung",
        "https://ts.huit.edu.vn/nganh-dh/nganh-thuong-mai-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-vat-lieu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-kinh-doanh-quoc-te",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-hoa-hoc",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-ly-tai-nguyen-va-moi-truong",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-khach-san",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-det-may",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-kinh-doanh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-dich-vu-du-lich-va-lu-hanh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-dieu-khien-va-tu-dong-hoa",
        "https://ts.huit.edu.vn/nganh-dh/nganh-tai-chinh-ngan-hang",
        "https://ts.huit.edu.vn/nganh-dh/nganh-ngon-ngu-anh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-an-toan-thong-tin",
    ]
    crawl_all(danh_sach_url)