import requests
from bs4 import BeautifulSoup
import csv
import os

def crawl_diemchuan_2024(url, output_file):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Tìm đúng table class MsoNormalTable, có 4 cột (STT, Mã ngành, Tên ngành, Điểm chuẩn)
    tables = soup.find_all("table", class_="MsoNormalTable")
    table = None
    for t in tables:
        # Kiểm tra số cột header
        first_row = t.find("tr")
        if first_row:
            cols = first_row.find_all("td")
            if len(cols) == 4:
                table = t
                break
    if not table:
        print("Không tìm thấy bảng dữ liệu đúng định dạng!")
        return
    rows = table.find_all("tr")
    data = []
    for row in rows:
        cols = row.find_all("td")
        cols = [col.get_text(strip=True) for col in cols]
        if len(cols) == 4:
            data.append(cols)
    os.makedirs('dataset', exist_ok=True)
    with open(os.path.join('dataset', output_file), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["STT", "Mã ngành", "Tên ngành", "Điểm chuẩn"])
        for row in data[1:]:  # Bỏ header
            writer.writerow(row)
    print(f"Đã lưu dữ liệu vào dataset/{output_file}")

if __name__ == "__main__":
    url = "https://ts.huit.edu.vn/tin-tuyen-sinh/diem-chuan-phuong-thuc-diem-thi-tot-nghiep-thpt-cua-truong-dai-hoc-cong-thuong-tp-hcm-nam-2024"
    crawl_diemchuan_2024(url, "diem-chuan-2024.csv")
