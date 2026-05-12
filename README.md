# TechPath AI – La bàn nghề nghiệp IT

TechPath AI là web app full-stack giúp người dùng khám phá lộ trình nghề nghiệp IT phù hợp thông qua bài đánh giá thông minh, sau đó tự động sinh roadmap học tập cá nhân hóa theo từng giai đoạn bằng AI.

## Tech Stack

- **Backend:** FastAPI (Python 3.9+) + SQLModel
- **Database:** SQLite (local) / PostgreSQL – Supabase (production)
- **AI:** OpenAI GPT-4o-mini qua LangChain (sinh roadmap + Socratic tutor chatbot)
- **Frontend:** HTMX + Bootstrap 5.3 + Jinja2 Templates
- **Auth:** Password (bcrypt) + Google OAuth
- **Deploy:** Render (Procfile sẵn sàng)

## Tính năng chính

- **Đánh giá nghề nghiệp đa bước:** Câu hỏi thích ứng theo path đã chọn hoặc "chưa biết – để AI gợi ý".
- **Khớp nghề bằng AI:** Tính điểm tin cậy cho 10 path IT (Software Engineer, Data Scientist, AI Engineer, Cybersecurity, Web, SysAdmin, Cryptographer, Blockchain, Game Dev, HCI).
- **Roadmap tương tác:** Timeline dọc với phase, checkpoint, dự án thực hành, resource (free/paid).
- **Theo dõi tiến độ:** Tick "Mark Done" cho từng checkpoint, % hoàn thành tự động cập nhật.
- **Chatbot Socratic Tutor:** Hỏi đáp theo phương pháp Socratic, có memory riêng cho từng user, mirror ngôn ngữ (Việt/Anh).
- **Đặt lại mật khẩu qua OTP email** (Gmail SMTP).

---

## Hướng dẫn chạy local

### 1. Cài dependency

Cần Python 3.9 trở lên. Sau khi clone repo:

```bash
pip install -r requirements.txt
```

### 2. Cấu hình biến môi trường

Tạo file `.env` ở thư mục gốc:

```env
# Bắt buộc – API key OpenAI để sinh roadmap + chatbot
OPENAI_API_KEY=sk-...

# Tuỳ chọn – nếu không có sẽ fallback SQLite (techpath.db)
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Tuỳ chọn – URL gốc cho Google OAuth redirect (mặc định http://localhost:8000)
BASE_URL=http://localhost:8000

# Tuỳ chọn – cấu hình gửi OTP quên mật khẩu (Gmail App Password)
SENDER_EMAIL=youremail@gmail.com
SENDER_PASSWORD=your-gmail-app-password
```

### 3. Seed dữ liệu demo (tuỳ chọn)

Tạo 3 user demo Alice/Bob/Carol với roadmap mẫu:

```bash
python seed.py
```

Script này **idempotent** – chạy nhiều lần không nhân đôi data. Nếu phát hiện đã có user demo sẽ skip.

### 4. Khởi động server

```bash
uvicorn main:app --reload --port 8000
```

Truy cập **http://127.0.0.1:8000**.

---

## Demo roadmap

3 user mẫu có roadmap sẵn (mật khẩu đăng nhập đều là `password123`):

| User | Email | Path |
|------|-------|------|
| Alice Johnson | alice@example.com | Software Engineer (9 tháng) |
| Bob Martinez | bob@example.com | Data Scientist (6 tháng) |
| Carol Chen | carol@example.com | AI Engineer (12 tháng) |

Xem trực tiếp roadmap qua route động (không phụ thuộc ID):

- http://127.0.0.1:8000/demo/alice
- http://127.0.0.1:8000/demo/bob
- http://127.0.0.1:8000/demo/carol

---

## Cấu trúc dự án

```
.
├── main.py              # Routing + business logic (auth, assessment, roadmap, chat)
├── models.py            # Bảng DB (User, Roadmap, Phase, Checkpoint, ChatMessage, ...)
├── database.py          # SQLAlchemy engine, fallback SQLite/PostgreSQL
├── helpers.py           # get_roadmap_data + get_model_response (gọi OpenAI sinh roadmap)
├── seed.py              # Seed demo Alice/Bob/Carol (idempotent)
├── migrate_tz_vn.py     # Migration 1-shot: shift timestamp cũ +7h sang giờ VN
├── requirements.txt
├── Procfile             # Cấu hình deploy Render
├── runtime.txt
├── templates/
│   ├── base.html, index.html, login.html, register.html, ...
│   ├── roadmap.html     # Trang chi tiết roadmap + timeline
│   └── partials/        # HTMX fragment cho update động
└── techpath.db          # SQLite local (auto-tạo khi chạy lần đầu)
```

---

## Triển khai production (Render + Supabase)

1. **Tạo PostgreSQL trên Supabase**, copy connection string (chọn pooler mode `Transaction` port 5432 hoặc `Session`).
2. **Deploy lên Render:**
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT` (đã có sẵn trong `Procfile`)
   - Environment variables: `OPENAI_API_KEY`, `DATABASE_URL`, `BASE_URL` (URL public của Render), `SENDER_EMAIL`, `SENDER_PASSWORD`
3. **Seed demo user (tuỳ chọn) bằng cách ssh vào Render shell hoặc chạy local trỏ vào DATABASE_URL prod:**
   ```bash
   python seed.py
   ```

---

## Lưu ý kỹ thuật

### Múi giờ

- Toàn bộ timestamp lưu DB là **giờ Việt Nam (UTC+7) dạng naive** thông qua `get_vietnam_time()` trong `models.py`.
- Khi xem qua Supabase Studio sẽ thấy đúng giờ VN (không phải UTC hay giờ Singapore).
- Nếu DB cũ còn timestamp UTC, chạy 1 lần:
  ```bash
  CONFIRM_TZ_MIGRATION=1 python migrate_tz_vn.py
  ```

### Demo roadmap link

Route `/demo/<name>` (alice/bob/carol) lookup theo email cố định rồi redirect tới roadmap thật. Nhờ vậy demo hoạt động bất kể ID auto-increment là 1, 3, hay 99.

### Google OAuth

`GOOGLE_CLIENT_ID` đang hardcode trong `main.py:54`. Muốn dùng credential khác, thay trực tiếp hoặc đẩy ra env var.

---

## Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|-----|------------|----------|
| `psycopg2.OperationalError: tenant/user not found` | DATABASE_URL Supabase sai hoặc project đã bị xoá | Kiểm tra lại connection string trong Supabase Dashboard |
| `Failed to generate roadmap from AI model` (500 khi submit assessment) | Thiếu/sai `OPENAI_API_KEY` | Set env var đúng và restart server |
| `Gửi email thất bại` (quên mật khẩu) | Gmail chặn login mật khẩu thường | Bật 2FA Gmail rồi tạo **App Password**, dùng password đó cho `SENDER_PASSWORD` |
| Bấm "See Demo" ra 404 | Chưa chạy `python seed.py` | Chạy seed |
| Roadmap.html lỗi 500 với ID không tồn tại | (Đã fix) | – |
