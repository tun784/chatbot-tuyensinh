import requests
from bs4 import BeautifulSoup
import csv
import os

def crawl_diemchuan_2022(url, output_file):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Tìm đúng table class MsoNormalTable, có 8 cột
    tables = soup.find_all("table", class_="MsoNormalTable")
    table = None
    for t in tables:
        first_row = t.find("tr")
        if first_row:
            cols = first_row.find_all("td")
            if len(cols) == 8:
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
        if len(cols) == 8:
            data.append(cols)
    os.makedirs('dataset', exist_ok=True)
    with open(os.path.join('dataset', output_file), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "TT", "Mã ngành", "Tên ngành", "Điểm chuẩn Điểm thi tốt nghiệp THPT",
            "Điểm chuẩn HB cả năm lớp 10, 11 & HK1 lớp 12", "Điểm chuẩn HB cả năm lớp 12",
            "Điểm chuẩn ĐGNL ĐHQG-HCM năm 2022", "Điểm chuẩn xét tuyển thẳng theo đề án riêng"
        ])
        for row in data[1:]:  # Bỏ header
            writer.writerow(row)
    print(f"Đã lưu dữ liệu vào dataset/{output_file}")

if __name__ == "__main__":
    url = "https://huit.edu.vn/nguoi-hoc/truong-dh-cong-nghiep-thuc-pham-tp-hcm-cong-bo-diem-chuan-trung-tuyen-nam-2022"
    crawl_diemchuan_2022(url, "diem-chuan-2022.csv")
