# 💰 QUẢN LÝ CHI TIÊU CÁ NHÂN

## 1. Giới thiệu

Phần mềm Quản lý chi tiêu cá nhân giúp người dùng theo dõi thu nhập, chi tiêu và quản lý tài chính cá nhân một cách thuận tiện.

Dự án được xây dựng bằng Python, sử dụng Streamlit để phát triển giao diện và FastAPI để xây dựng hệ thống API.

## 2. Công nghệ sử dụng

- **Python:** Ngôn ngữ lập trình chính.
- **Streamlit:** Xây dựng giao diện người dùng.
- **FastAPI:** Xây dựng REST API.
- **SQLModel / SQLAlchemy:** Quản lý dữ liệu.
- **PostgreSQL (Neon):** Lưu trữ dữ liệu trực tuyến.
- **SQLite:** Cơ sở dữ liệu sử dụng khi phát triển local.
- **Pandas / Altair:** Xử lý dữ liệu và trực quan hóa thống kê.
- **GitHub:** Quản lý mã nguồn.

## 3. Chức năng chính

- Đăng ký và đăng nhập tài khoản.
- Quản lý thông tin tài khoản.
- Quản lý danh mục thu nhập và chi tiêu.
- Thêm, sửa, xóa giao dịch.
- Theo dõi lịch sử giao dịch.
- Thống kê thu nhập, chi tiêu và số dư.
- Trực quan hóa dữ liệu bằng biểu đồ.
- Nhập dữ liệu từ CSV.
- Xuất dữ liệu sang Excel.
- Quản lý dữ liệu thông qua API.

## 4. Cấu trúc dự án

```text
QuanLyChiTieuCaNhan/
│
├── api.py
├── api_client.py
├── config.py
├── database.py
├── main.py
├── app.py
├── models.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── services/
│   ├── auth_service.py
│   ├── budget_service.py
│   ├── category_service.py
│   ├── data_service.py
│   ├── export_service.py
│   ├── statistics_service.py
│   └── transaction_service.py
│
├── utils/
│   ├── formatters.py
│   ├── api_errors.py
│   ├── page_context.py
│   ├── session.py
│   ├── ui_helpers.py
│   └── validators.py
│
├── pages/
│   ├── auth.py
│   ├── dashboard.py
│   ├── transactions.py
│   ├── categories.py
│   ├── budget.py
│   ├── statistics.py
│   ├── profile.py
│   └── export.py
│
├── components/
│   ├── sidebar.py
│   ├── stat_cards.py
│   ├── charts.py
│   ├── transaction_table.py
│   ├── transaction_form.py
│   ├── category_card.py
│   └── notifications.py
│
├── styles/
│   ├── style.css
│   ├── auth.css
│   ├── dashboard.css
│   ├── transactions.css
│   ├── income.css
│   ├── expense.css
│   ├── categories.css
│   ├── statistics.css
│   ├── export.css
│   ├── profile.css
│   └── style_backup.css
│
├── data/
│
└── venv/
```

`main.py` là entry point tối giản của Streamlit. `app.py` chỉ khởi tạo session,
nạp CSS và điều hướng tới các trang. `legacy_ui.py` chỉ còn là marker tương
thích 7 dòng; toàn bộ mã thực thi đã được chuyển sang `pages/`, `components/`,
`services/` và `utils/`. Giao diện dùng CSS chung và CSS theo trang.

## 5. Cài đặt dự án

### Bước 1: Clone repository

```bash
git clone https://github.com/Huynhbao19092006/QuanLyChiTieuCaNhan.git
```

### Bước 2: Di chuyển vào thư mục dự án

```bash
cd QuanLyChiTieuCaNhan
```

### Bước 3: Tạo môi trường ảo

Windows:

```powershell
python -m venv venv
venv\Scripts\activate
```

### Bước 4: Cài đặt thư viện

```bash
pip install -r requirements.txt
```

## 6. Cấu hình môi trường

Tạo file `.env` tại thư mục gốc dự án.

Ví dụ:

```env
ENVIRONMENT=development
SECRET_KEY=your_secret_key_here
DATABASE_URL=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Lưu ý:

- Khi sử dụng PostgreSQL, điền chuỗi kết nối Neon vào `DATABASE_URL`.
- Không chia sẻ file `.env` hoặc đưa thông tin bí mật lên GitHub.
- Khi triển khai production, cần cấu hình biến môi trường riêng trên máy chủ.

## 7. Khởi chạy chương trình

### Khởi chạy FastAPI

```bash
python -m uvicorn api:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Tài liệu API:

```text
http://127.0.0.1:8000/docs
```

### Khởi chạy Streamlit

Mở một Terminal khác:

```bash
streamlit run main.py
```

Giao diện:

```text
http://localhost:8501
```

## 8. Tác giả

**Dự án:** Quản lý chi tiêu cá nhân

**Ngôn ngữ:** Python

**Mục đích:** Hỗ trợ quản lý thu nhập, chi tiêu và theo dõi tình hình tài chính cá nhân.

---

© 2026 Quản lý chi tiêu cá nhân.