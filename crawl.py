import requests
import unicodedata
from bs4 import BeautifulSoup
import re
import os
import json
headers = {
    "User-Agent": "Mozilla/5.0"
}

# Hàm loại bỏ phần footer không cần thiết
def clean_html_footer(html):
    # Cắt bỏ đoạn cuối nếu có cụm này
    parts = re.split(r"Để biết thêm thông tin tuyển sinh", html, flags=re.IGNORECASE)
    return parts[0]

def remove_accents(text):
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# Hàm trích xuất Mã ngành từ HTML
def extract_ma_nganh(soup):
    candidates = soup.find_all(string=re.compile(r"Mã ngành[:\s]?", re.IGNORECASE))
    for txt in candidates:
        full = txt.strip()
        # Trường hợp mã nằm cùng text
        m = re.search(r"\d{6,}", full)
        if m:
            return m.group(0)
        # Trường hợp mã ở thẻ kế tiếp
        if txt.parent:
            sib = txt.parent.find_next_sibling(string=re.compile(r"\d{6,}"))
            if sib:
                m2 = re.search(r"\d{6,}", sib.strip())
                if m2:
                    return m2.group(0)
    return None

def crawl_page(url):
    print(f">>> Đang crawl: {url}")
    response = requests.get(url, headers=headers)
    response.encoding = "utf-8"  # Đảm bảo đọc tiếng Việt
    raw_html = clean_html_footer(response.text)
    soup = BeautifulSoup(raw_html, "html.parser")

    ma_nganh = extract_ma_nganh(soup)

    output_lines = []

    title_tag = soup.find("h1")
    if title_tag:
        title = title_tag.get_text(strip=True)
        output_lines.append(f"{title}")

    # print(soup.prettify())

    # Xử lý phần sau mã ngành
    deepest_spans = []
    for p in soup.find_all('p'):
        if any(x in p.get_text() for x in ["MÃ NGÀNH:", "Mã ngành:", "mã ngành:"]):
            ma_nganh_p = p
            next_p = ma_nganh_p.find_next_sibling('p')
            if next_p:
                inner_spans = next_p.find_all('span')
                for span in inner_spans:
                    if not span.find('span'):
                        text = span.get_text(strip=True)
                        if text:
                            deepest_spans.append(text)
            break

    if deepest_spans:
        output_lines.append(" ".join(deepest_spans))
    else:
        output_lines.append("Không tìm thấy thẻ <span> trong cùng trong thẻ <p> ngay sau thẻ chứa 'MÃ NGÀNH'.")

    # Xử lý nội dung chính + điều kiện tuyển sinh
    main_content = []
    extra_content = []
    found_condition = False

    for p in soup.select('p.MsoNormal'):
        text = p.get_text(strip=True)
        if not text:
            continue
        main_content.append(text)

        if "3. ĐIỀU KIỆN TUYỂN SINH" in text.upper() and not found_condition:
            found_condition = True
            tr_current = p.find_parent('tr')
            if tr_current:
                tr_next = tr_current.find_next_sibling('tr')
                if tr_next:
                    p_tags = tr_next.find_all('p')
                    for p_tag in p_tags:
                        spans = p_tag.find_all('span')
                        if spans:
                            for span in spans:
                                span_text = span.get_text(strip=True)
                                if span_text:
                                    extra_content.append(span_text)
                        else:
                            p_text = p_tag.get_text(strip=True)
                            if p_text:
                                extra_content.append(p_text)

    for line in main_content:
        output_lines.append(line)
        if "3. ĐIỀU KIỆN TUYỂN SINH" in line.upper() and extra_content:
            output_lines.extend(extra_content)

    return {
        "url": url,
        "ma_nganh": ma_nganh,
        "title": title if title_tag else None,
        "noidung": "\n".join(output_lines)
    }

def slugify(text):
    """Chuyển mã ngành hoặc tên ngành thành tên file hợp lệ"""
    return re.sub(r'[^a-zA-Z0-9_-]', '_', text).lower()

def crawl_all(urls, output_dir="data/output_txt"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for idx, url in enumerate(urls):
        try:
            data = crawl_page(url)
            # Tạo tên file: mã ngành hoặc số thứ tự
            if data["title"]:
                filename = f"{slugify(remove_accents(data['title']))}.txt"
            else:
                filename = f"nganh_{idx + 1}.txt"
            path = os.path.join(output_dir, filename)

            with open(path, "w", encoding="utf-8") as f:
                f.write(f"URL: {data['url']}\n")
                if data["ma_nganh"]:
                    f.write(f"Mã ngành: {data['ma_nganh']}\n\n")
                f.write(data["noidung"])

            print(f"✅ Đã lưu: {filename}")
        except Exception as e:
            print(f"[!] Lỗi khi crawl {url}: {e}")

if __name__ == "__main__":
    danh_sach_url = [
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-thong-tin",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-co-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-dam-bao-chat-luong-va-an-toan-thuc-pham",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-dien-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-tai-chinh-ngan-hang",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-sinh-hoc",
        "https://ts.huit.edu.vn/nganh-dh/nganh-ngon-ngu-anh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-luat-kinh-te",
        "https://ts.huit.edu.vn/nganh-dh/nganh-logistic-va-quan-ly-chuoi-cung-ung",
        "https://ts.huit.edu.vn/nganh-dh/nganh-thuong-mai-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-vat-lieu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-luat.",
        "https://ts.huit.edu.vn/nganh-dh/nganh-kinh-doanh-quoc-te",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-hoa-hoc",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-ly-tai-nguyen-va-moi-truong",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-co-dien-tu",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-khach-san",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-kinh-doanh-thuc-pham",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-det-may",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-kinh-doanh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-luat-kinh-te",
        "https://ts.huit.edu.vn/nganh-dh/nganh-quan-tri-dich-vu-du-lich-va-lu-hanh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-ky-thuat-dieu-khien-va-tu-dong-hoa",
        "https://ts.huit.edu.vn/nganh-dh/nganh-dam-bao-chat-luong-va-an-toan-thuc-pham",
        "https://ts.huit.edu.vn/nganh-dh/nganh-tai-chinh-ngan-hang",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-sinh-hoc",
        "https://ts.huit.edu.vn/nganh-dh/nganh-ngon-ngu-anh",
        "https://ts.huit.edu.vn/nganh-dh/nganh-cong-nghe-tai-chinh-fintech",
        "https://ts.huit.edu.vn/nganh-dh/nganh-an-toan-thong-tin",
        "https://ts.huit.edu.vn/nganh-dh/nganh-khoa-hoc-dinh-duong-va-am-thuc"
    ]
    crawl_all(danh_sach_url)

# # ✅ Ghi toàn bộ output vào file
# with open("che-tao-may.txt", "w", encoding="utf-8") as f:
#     for line in output_lines:
#         f.write(line + "\n")

# # ✅ In ra màn hình nếu muốn kiểm tra nhanh
# for line in output_lines:
#     print(line)
