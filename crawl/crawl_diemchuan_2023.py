import requests
from bs4 import BeautifulSoup
import csv
import os

def crawl_diemchuan_2023(url, output_file):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Tìm table có border=1 và width=100%
    table = soup.find("table", {"border": "1", "width": "100%"})
    if not table:
        print("Không tìm thấy bảng dữ liệu!")
        return
    rows = table.find_all("tr")
    data = []
    for row in rows:
        cols = row.find_all("td")
        cols = [col.get_text(strip=True) for col in cols]  # Giữ nguyên dấu tiếng Việt
        if len(cols) >= 4:
            data.append(cols[:4])
    os.makedirs('dataset', exist_ok=True)
    with open(os.path.join('dataset', output_file), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["STT", "Mã ngành", "Tên ngành", "Điểm chuẩn", "Năm"])
        for row in data[1:]:  # Bỏ header
            row.append("2023")
            writer.writerow(row)
    print(f"Đã lưu dữ liệu vào dataset/{output_file}")

if __name__ == "__main__":
    url = "https://ts.huit.edu.vn/tin-tuyen-sinh/diem-chuan-2023-phuong-thuc-diem-thi-tot-nghiep-thpt-cua-truong-dh-cong-thuong-tphcm"
    crawl_diemchuan_2023(url, "diem-chuan-2023.csv")
