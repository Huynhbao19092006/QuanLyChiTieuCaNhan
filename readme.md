## 1. Cài đặt

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Chạy ứng dụng

```bash
python app.py
```

Mở trình duyệt tại **http://127.0.0.1:5000**

## 3. Sử dụng

1. Chọn loại tài liệu (7 loại có sẵn).
2. Tải lên file dữ liệu `.csv` / `.xlsx` / `.xls` / `.json` — hoặc tải file
   mẫu ở cuối trang chủ để xem đúng cấu trúc cột cần có.
3. Bấm **"Sinh PDF hàng loạt"**.
4. Xem bảng kết quả: dòng nào thành công (có link tải PDF riêng), dòng nào
   bị bỏ qua kèm lý do lỗi cụ thể.
5. Tải toàn bộ PDF dưới dạng `.zip`, hoặc tải file `.log` để lưu vết.

## 4. Cấu trúc thư mục kết quả

Mỗi lượt chạy được lưu vào một thư mục riêng theo mã lượt chạy để tránh
đè lên lượt chạy trước, bên trong vẫn giữ đúng cấu trúc `<loại>/*.pdf` như
yêu cầu:

```
output/
 └── 20260917_143000_ab12cd/
      └── salary/
           ├── NV001.pdf
           ├── NV002.pdf
           ├── NV003.pdf
           └── salary.zip
logs/
 └── log_20260917_143000_ab12cd.log
```

## 5. Kiến trúc mã nguồn

```
app.py                 Flask: routes, upload, tải kết quả
config.py               Cấu hình 7 loại tài liệu: cột bắt buộc, công thức
                         tính toán, nhãn hiển thị, dữ liệu mẫu
utils/
  data_loader.py         Đọc CSV/Excel/JSON -> pandas.DataFrame
  validators.py           Kiểm tra cột bắt buộc + kiểm tra từng dòng dữ liệu
  calculators.py          Bọc try...except quanh công thức tính toán
  pdf_generator.py        Dựng PDF bằng reportlab, có nhúng font Unicode
                           (DejaVu Sans) để hiển thị đúng tiếng Việt có dấu
  generator.py             Điều phối toàn bộ luồng: đọc -> kiểm tra -> tính
                           -> sinh PDF -> ghi log, xử lý lỗi từng dòng độc lập
  logger_setup.py          Cấu hình logging ra file + console cho mỗi lượt chạy
templates/               Giao diện web (Jinja2)
static/                  CSS + font DejaVu Sans dùng để nhúng vào PDF
sample_data/              Nơi lưu các file CSV mẫu được sinh khi người dùng
                          bấm "Tải file mẫu" lần đầu
```

## 6. Thêm loại tài liệu mới

Chỉ cần thêm một dict cấu hình mới trong `config.py` (theo mẫu các loại có
sẵn) rồi thêm vào danh sách `DOCUMENT_TYPES` ở cuối file — không cần sửa
`app.py` hay giao diện, hệ thống sẽ tự động hiển thị loại tài liệu mới trên
trang chủ.

## 7. Xử lý lỗi & log

- Nếu file thiếu hẳn một cột bắt buộc -> dừng toàn bộ lượt chạy, báo lỗi rõ
  ràng (thiếu cột gì).
- Nếu một dòng dữ liệu bị thiếu giá trị hoặc sai kiểu số -> **chỉ dòng đó**
  bị bỏ qua và ghi log lỗi, các dòng còn lại vẫn được xử lý bình thường.
- Mọi lỗi trong quá trình tính toán hoặc sinh PDF đều được bọc trong
  `try...except` để không làm crash toàn bộ chương trình.
- Toàn bộ log (thành công lẫn thất bại, có timestamp) được ghi vào file
  `.log` riêng cho từng lượt chạy, tải về được từ trang kết quả.

## 8. Ghi chú

- Font tiếng Việt: dự án nhúng sẵn `DejaVu Sans` (font Unicode mã nguồn mở)
  trong `static/fonts/` để đảm bảo PDF hiển thị đúng dấu tiếng Việt trên mọi
  máy, không phụ thuộc font hệ thống.
- `RUN_REGISTRY` trong `app.py` lưu tạm thông tin lượt chạy trong bộ nhớ —
  phù hợp cho demo/đồ án. Nếu triển khai thật, nên thay bằng cơ sở dữ liệu.
