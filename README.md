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

#### 📋 Hướng dẫn chi tiết từng biến môi trường

##### **OPENAI_API_KEY** (Bắt buộc)
Cần thiết để tạo roadmap AI và chatbot Socratic Tutor.
1. Truy cập https://platform.openai.com/account/api-keys
2. Đăng nhập/tạo tài khoản OpenAI (có thể dùng Gmail hoặc GitHub)
3. Nhấp **"Create new secret key"** → Copy key
4. Dán vào `.env`: `OPENAI_API_KEY=sk-...`
5. **Lưu ý:** Giữ bí mật key, không commit lên Git

##### **DATABASE_URL** (Tuỳ chọn)
- **Không set:** Hệ thống tự động dùng **SQLite local** (`techpath.db`) – phù hợp dev/demo
- **Muốn dùng PostgreSQL (Supabase):**
  1. Tạo project tại https://supabase.com
  2. Vào **Settings → Database** → Copy **Connection string** (chọn mode `Transaction`)
  3. Format: `postgresql://[user]:[password]@[host]:[port]/[database]`
  4. Dán vào `.env`: `DATABASE_URL=postgresql://...`
  5. Khi deploy lên production khuyên dùng Supabase thay SQLite

##### **BASE_URL** (Tuỳ chọn)
- **Local dev (mặc định):** `http://localhost:8000` – để trống hoặc bỏ dòng này
- **Production (Render):** `https://your-app-name.onrender.com` – cần thiết cho Google OAuth redirect đúng

##### **SENDER_EMAIL & SENDER_PASSWORD** (Tuỳ chọn)
Cần thiết để gửi OTP reset mật khẩu qua email. **Chỉ hỗ trợ Gmail + App Password** (không phải mật khẩu tài khoản thường).

**Cách setup Gmail:**
1. **Bật 2-Factor Authentication:**
   - Vào https://myaccount.google.com/security
   - Chọn **2-Step Verification** → Bật nó
   
2. **Tạo App Password:**
   - Quay lại Security → Cuộn xuống **App passwords** (chỉ hiện khi bật 2FA)
   - Chọn **Mail** → **Windows Computer** (hoặc thiết bị của bạn)
   - Google tạo **16 ký tự password** → Copy (không có dấu cách)
   
3. **Cập nhật `.env`:**
   ```env
   SENDER_EMAIL=your-gmail@gmail.com
   SENDER_PASSWORD=xxxx xxxx xxxx xxxx
   ```
   (Paste đúng như Google cấp, kể cả dấu cách)

4. **Test gửi email:** Bấm "Forgot Password" trên login page để test

##### **GOOGLE_CLIENT_ID** (Google OAuth - hardcode trong code)
Hiện tại hardcode trong `main.py:54` cho demo. Để dùng credential Google khác:
1. Tạo OAuth 2.0 credentials tại https://console.cloud.google.com
2. Tạo **OAuth 2.0 Client ID** (loại Web application)
3. Thêm **Authorized redirect URIs:**
   - `http://localhost:8000/auth/google/callback` (dev)
   - `https://your-app-name.onrender.com/auth/google/callback` (production)
4. Copy **Client ID** → Mở `main.py` dòng 54 → Replace `GOOGLE_CLIENT_ID` value

---

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

| User | Email | Password | Path |
|------|-------|------|------|
| Alice Johnson | alice@example.com | password123 | Software Engineer (9 tháng) |
| Bob Martinez | bob@example.com | password123 |Data Scientist (6 tháng) |
| Carol Chen | carol@example.com | password123 |AI Engineer (12 tháng) |

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

### Đăng nhập Google OAuth

**⚠️ Cần setup trước khi dùng tính năng "Đăng nhập bằng Google"**

Chi tiết xem phần **[GOOGLE_CLIENT_ID](#google_client_id-google-oauth---hardcode-trong-code)** ở trên.

**Tóm tắt:**
1. Tạo OAuth 2.0 credentials tại https://console.cloud.google.com
2. Thêm redirect URI: `http://localhost:8000/auth/google/callback` (dev) hoặc `https://your-app-name.onrender.com/auth/google/callback` (prod)
3. Copy Client ID → Cập nhật `GOOGLE_CLIENT_ID` trong `main.py:54`

---

## Troubleshooting

| Lỗi | Nguyên nhân | Cách fix |
|-----|------------|----------|
| `psycopg2.OperationalError: tenant/user not found` | DATABASE_URL Supabase sai hoặc project đã bị xoá | Kiểm tra lại connection string trong Supabase Dashboard |
| `Failed to generate roadmap from AI model` (500 khi submit assessment) | Thiếu/sai `OPENAI_API_KEY` | Set env var đúng và restart server |
| `Gửi email thất bại` (quên mật khẩu) | Gmail chặn login mật khẩu thường hoặc chưa bật 2FA | Bật 2FA Gmail rồi tạo **App Password**, dùng password đó cho `SENDER_PASSWORD` |
| `SMTPAuthenticationError: 535 5.7.8 Username and Password not accepted` | SENDER_PASSWORD sai hoặc chưa tạo App Password | Xem hướng dẫn **SENDER_EMAIL & SENDER_PASSWORD** ở trên |
| Bấm "See Demo" ra 404 | Chưa chạy `python seed.py` | Chạy seed |
| Roadmap.html lỗi 500 với ID không tồn tại | (Đã fix) | – |
| `OIDC error` khi login Google (local dev) | Redirect URI chưa config hoặc GOOGLE_CLIENT_ID sai | Kiểm tra [BASE_URL](#base_url-tuỳ-chọn) và cập nhật Google Console redirect URIs |
| `.env` không được load, env var trống | File `.env` chưa được tạo hoặc đặt sai vị trí | Tạo file `.env` ở **thư mục gốc** (cùng cấp `main.py`), không phải subfolder |
| `FileNotFoundError: .env` khi chạy `python seed.py` | .env chưa tồn tại | Tạo `.env` từ template [.env.example](.env.example) trước khi chạy bất kỳ script nào |
