"""
main.py – TechPath AI FastAPI application
"""
import json
import uuid
import hashlib
from passlib.context import CryptContext
import smtplib
import ssl
import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from database import create_db_and_tables, get_session
from models import (
    User, Assessment, MatchResult, Roadmap,
    Phase, Checkpoint, ProjectIdea, Resource,
    PasswordResetToken, get_vietnam_time,
    ChatThread, ChatMessage, UserMemory
)
from helpers import get_roadmap_data, get_model_response

import urllib.parse

# Cấu hình băm mật khẩu
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cấu hình Google
GOOGLE_CLIENT_ID = "551158881077-om6jbecbdlhh4eg0179je47k3jbf3s8i.apps.googleusercontent.com"

app = FastAPI(title="TechPath AI")
templates = Jinja2Templates(directory="templates")
templates.env.globals['unquote'] = urllib.parse.unquote
templates.env.globals['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID


@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    
    # Auto-migration for SQLite (ép buộc thêm cột nếu thiếu)
    import sqlite3
    try:
        conn = sqlite3.connect("techpath.db")
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "password_hash" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN password_hash VARCHAR")
            print("Migration: Added password_hash column to user table")
            
        if "created_at" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN created_at DATETIME")
            print("Migration: Added created_at column to user table")
            
        # New Career Fields
        if "current_status" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN current_status VARCHAR")
        if "primary_skills" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN primary_skills VARCHAR")
        if "career_goal" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN career_goal VARCHAR")
        if "hours_per_week" not in columns:
            cursor.execute("ALTER TABLE user ADD COLUMN hours_per_week INTEGER")
            
        # UserMemory table migration
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='usermemory'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE usermemory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE REFERENCES user(id),
                    summary TEXT NOT NULL DEFAULT '',
                    key_facts TEXT NOT NULL DEFAULT '[]',
                    updated_at DATETIME
                )
            """)
            print("Migration: Created usermemory table")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

# ── Pages ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, session: Session = Depends(get_session)):
    user_id = request.cookies.get("session_token")
    user = None
    if user_id:
        try:
            user = session.exec(select(User).where(User.id == int(user_id))).first()
        except:
            pass
    return templates.TemplateResponse(request, "index.html", {"user": user})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session)
):
    email = email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password"})
    
    if not user.password_hash or not pwd_context.verify(password, user.password_hash):
        return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password"})
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session_token", str(user.id))
    response.set_cookie("session_user_name", urllib.parse.quote(user.name))
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html")

@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session)
):
    if password != confirm_password:
        return templates.TemplateResponse(request, "register.html", {"error": "Passwords do not match"})
        
    email = email.strip().lower()
    existing = session.exec(select(User).where(User.email == email)).first()
    if existing:
        return templates.TemplateResponse(request, "register.html", {"error": "Email already registered"})
    
    hashed = pwd_context.hash(password)
    user = User(name=name, email=email, password_hash=hashed)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session_token", str(user.id))
    response.set_cookie("session_user_name", urllib.parse.quote(user.name))
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session_token")
    response.delete_cookie("session_user_name")
    return response

@app.post("/auth/google")
async def google_auth(
    request: Request,
    credential: str = Form(...),
    session: Session = Depends(get_session)
):
    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        # Verify without strict audience here, or user must replace it. 
        # But we'll use a placeholder and catch Audience missing errors, but let's just 
        # instruct the user to update `YOUR_GOOGLE_CLIENT_ID`
        idinfo = id_token.verify_oauth2_token(
            credential, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
        
        email = idinfo['email'].strip().lower()
        name = idinfo.get('name', 'Google User')
        
        user = session.exec(select(User).where(User.email == email)).first()
        if not user:
            user = User(name=name, email=email)
            session.add(user)
            session.commit()
            session.refresh(user)
            
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie("session_token", str(user.id))
        response.set_cookie("session_user_name", urllib.parse.quote(user.name))
        return response
    except ValueError as e:
        print(f"Google Token Verification Error: {e}")
        return templates.TemplateResponse(request, "login.html", {"error": f"Google Sign-In failed: Invalid token or Client ID mismatch. Details: {str(e)}"})
    except Exception as e:
        return templates.TemplateResponse(request, "login.html", {"error": f"Google Sign-In failed: {str(e)}"})


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("session_token")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Lấy lịch sử Roadmap
    roadmaps = session.exec(select(Roadmap).where(Roadmap.user_id == user.id).order_by(Roadmap.created_at.desc())).all()
    
    return templates.TemplateResponse(request, "settings.html", {"user": user, "roadmaps": roadmaps})

@app.post("/settings/profile", response_class=HTMLResponse)
async def settings_profile_post(
    request: Request,
    name: str = Form(...),
    current_status: Optional[str] = Form(None),
    primary_skills: Optional[str] = Form(None),
    career_goal: Optional[str] = Form(None),
    hours_per_week: Optional[int] = Form(None),
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("session_token")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    user.name = name
    user.current_status = current_status
    user.primary_skills = primary_skills
    user.career_goal = career_goal
    user.hours_per_week = hours_per_week
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    roadmaps = session.exec(select(Roadmap).where(Roadmap.user_id == user.id).all())
    return templates.TemplateResponse(request, "settings.html", {
        "user": user, 
        "roadmaps": roadmaps,
        "profile_success": "Đã cập nhật hồ sơ thành công!"
    })

@app.post("/settings/password", response_class=HTMLResponse)
async def settings_password_post(
    request: Request,
    current_password: Optional[str] = Form(None),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session)
):
    user_id = request.cookies.get("session_token")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user = session.exec(select(User).where(User.id == int(user_id))).first()
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Validation
    if new_password != confirm_password:
        return templates.TemplateResponse(request, "settings.html", {"user": user, "error": "Mật khẩu mới không khớp"})
    
    # If user already has a password, verify it
    if user.password_hash:
        if not current_password or not pwd_context.verify(current_password, user.password_hash):
            return templates.TemplateResponse(request, "settings.html", {"user": user, "error": "Mật khẩu hiện tại không đúng"})
    
    # Update password
    user.password_hash = pwd_context.hash(new_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    
    return templates.TemplateResponse(request, "settings.html", {"user": user, "success": "Đã cập nhật mật khẩu thành công!"})



SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "tanhlucky102@gmail.com" 
SENDER_PASSWORD = "fhbc wbub bxhu rlfr" 

def send_otp_email(to_email: str, otp_code: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Mã xác thực TechPath AI - Quên mật khẩu"
    message["From"] = SENDER_EMAIL
    message["To"] = to_email

    text = f"Mã OTP của bạn là: {otp_code}. Mã này có hiệu lực trong 5 phút."
    html = f"""
    <html>
    <body>
        <h2 style='color: #4f46e5;'>TechPath AI</h2>
        <p>Chào bạn,</p>
        <p>Bạn đã yêu cầu đặt lại mật khẩu. Vui lòng sử dụng mã OTP dưới đây:</p>
        <div style='background-color: #f3f4f6; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px;'>
            {otp_code}
        </div>
        <p>Mã này sẽ hết hạn sau 5 phút.</p>
        <p>Nếu bạn không yêu cầu điều này, hãy bỏ qua email này.</p>
    </body>
    </html>
    """
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, message.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "forgot_password.html")

@app.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_post(
    request: Request,
    email: str = Form(...),
    session: Session = Depends(get_session)
):
    email = email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()
    
    if not user:
        return templates.TemplateResponse(request, "forgot_password.html", {"error": "Email không tồn tại trong hệ thống"})
    
    # Tạo mã OTP 6 số
    otp = ''.join(random.choices(string.digits, k=6))
    expires = get_vietnam_time() + timedelta(minutes=5)
    
    # Lưu vào database
    reset_token = PasswordResetToken(user_id=user.id, otp_code=otp, expires_at=expires)
    session.add(reset_token)
    session.commit()
    
    # Gửi mail
    if send_otp_email(email, otp):
        response = RedirectResponse(url=f"/verify-otp?email={email}", status_code=303)
        return response
    else:
        return templates.TemplateResponse(request, "forgot_password.html", {"error": "Gửi email thất bại, vui lòng thử lại sau. (Vui lòng kiểm tra lại cấu hình SENDER_EMAIL)"})

@app.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_page(request: Request, email: str):
    return templates.TemplateResponse(request, "verify_otp.html", {"email": email})

@app.post("/verify-otp", response_class=HTMLResponse)
async def verify_otp_post(
    request: Request,
    email: str = Form(...),
    otp: str = Form(...),
    session: Session = Depends(get_session)
):
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return templates.TemplateResponse(request, "verify_otp.html", {"email": email, "error": "Đã có lỗi xảy ra"})
        
    # Lấy mã OTP mới nhất của user này
    db_token = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.created_at.desc())
    ).first()
    
    if not db_token or db_token.otp_code != otp:
        return templates.TemplateResponse(request, "verify_otp.html", {"email": email, "error": "Mã OTP không chính xác"})
    
    if get_vietnam_time() > db_token.expires_at:
        return templates.TemplateResponse(request, "verify_otp.html", {"email": email, "error": "Mã OTP đã hết hạn"})
    
    # OK, chuyển sang trang đổi mật khẩu (truyền otp kèm để bảo mật nhẹ)
    return RedirectResponse(url=f"/reset-password?email={email}&token={otp}", status_code=303)

@app.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, email: str, token: str):
    return templates.TemplateResponse(request, "reset_password.html", {"email": email, "token": token})

@app.post("/reset-password", response_class=HTMLResponse)
async def reset_password_post(
    request: Request,
    email: str = Form(...),
    token: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    session: Session = Depends(get_session)
):
    if password != confirm_password:
        return templates.TemplateResponse(request, "reset_password.html", {"email": email, "token": token, "error": "Mật khẩu không khớp"})
        
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return templates.TemplateResponse(request, "login.html", {"error": "Lỗi hệ thống"})
        
    db_token = session.exec(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id, PasswordResetToken.otp_code == token)
    ).first()
    
    if not db_token:
        return templates.TemplateResponse(request, "login.html", {"error": "Yêu cầu không hợp lệ"})
        
    # Cập nhật mật khẩu
    user.password_hash = pwd_context.hash(password)
    session.add(user)
    
    # Xoá token đã dùng
    session.delete(db_token)
    session.commit()
    
    return templates.TemplateResponse(request, "login.html", {"message": "Đổi mật khẩu thành công! Vui lòng đăng nhập."})


@app.get("/assessment", response_class=HTMLResponse)
async def assessment(request: Request):
    return templates.TemplateResponse(request, "assessment.html", {
        "step": 1,
    })


@app.get("/roadmap/{roadmap_id}", response_class=HTMLResponse)
async def roadmap_page(
    request: Request,
    roadmap_id: int,
    session: Session = Depends(get_session),
):
    roadmap, user, phase_data = get_roadmap_data(roadmap_id, session)
    if roadmap is None:
        raise HTTPException(status_code=404, detail="Roadmap not found")

    # Fetch match result for recommended path info
    assessment_obj = session.get(Assessment, roadmap.assessment_id)
    match_result = None
    top_matches = []
    if assessment_obj:
        match_result = session.exec(
            select(MatchResult).where(MatchResult.assessment_id == assessment_obj.id)
        ).first()
        if match_result:
            top_matches = sorted(
                json.loads(match_result.top_matches),
                key=lambda x: x["score"],
                reverse=True,
            )

    return templates.TemplateResponse(request, "roadmap.html", {
        "roadmap": roadmap,
        "user": user,
        "phase_data": phase_data,
        "top_matches": top_matches,
        "match_result": match_result,
    })


@app.get("/api/roadmap/{roadmap_id}/progress")
async def get_roadmap_progress(
    roadmap_id: int,
    session: Session = Depends(get_session),
):
    roadmap = session.get(Roadmap, roadmap_id)
    if not roadmap:
        raise HTTPException(status_code=404, detail="Roadmap not found")
    return {"progress": roadmap.overall_progress}


# ── HTMX Quiz Step Endpoints ───────────────────────────────────────────────────

CAREER_PATHS = [
    "Software Engineer",
    "Data Scientist",
    "Cybersecurity Engineer",
    "Web Developer",
    "Systems Administrator",
    "Cryptographer",
    "Blockchain Developer",
    "Artificial Intelligence (AI) Engineer",
    "Game Developer",
    "Human-Computer Interaction (HCI) Specialist",
    "Not yet known – I want TechPath AI to recommend the best fit for me",
]

JOB_SKILLS = {
    "Software Engineer": [
        "Programming (Python/Java/C++/etc.)",
        "Algorithms & data structures",
        "Git & version control",
        "Testing & debugging",
        "Cloud platforms (AWS/Azure)",
        "Databases (SQL/NoSQL)",
        "Clean code & design patterns",
        "APIs & microservices",
    ],
    "Data Scientist": [
        "Python or R",
        "Statistics & probability",
        "Machine-learning algorithms",
        "Data visualization (Tableau/Matplotlib)",
        "SQL & big-data tools",
        "Model training & evaluation",
        "Data cleaning & feature engineering",
        "Ethics in data science",
    ],
    "Cybersecurity Engineer": [
        "Networking fundamentals",
        "Encryption & cryptographic protocols",
        "Penetration testing & ethical hacking",
        "Security tools (Wireshark, Nmap, Metasploit)",
        "Risk assessment & compliance",
        "Linux command line & scripting",
        "Firewall & intrusion detection",
        "Vulnerability management",
    ],
    "Web Developer": [
        "HTML/CSS/JavaScript",
        "Front-end frameworks (React/Vue)",
        "Back-end (Node.js/Python/PHP)",
        "Databases & APIs",
        "Responsive & mobile-first design",
        "Version control & deployment",
        "Web security basics",
        "Performance optimization",
    ],
    "Systems Administrator": [
        "Linux/Windows server admin",
        "Networking & infrastructure",
        "Cloud & virtualization",
        "Automation scripting (Bash/PowerShell)",
        "Backup & disaster recovery",
        "Monitoring & troubleshooting",
        "User access & security",
        "Containerization (Docker/K8s)",
    ],
    "Cryptographer": [
        "Advanced mathematics (number theory/linear algebra)",
        "Cryptographic algorithms (RSA/AES/ECC)",
        "Crypto libraries & implementation",
        "Quantum & post-quantum concepts",
        "Security proofs & formal verification",
        "Threat modeling",
        "Research paper reading",
        "Blockchain primitives",
    ],
    "Blockchain Developer": [
        "Solidity smart contracts",
        "Ethereum / other blockchain platforms",
        "Cryptography basics",
        "DApp front-end integration (Web3.js)",
        "Consensus mechanisms",
        "Smart-contract auditing & testing",
        "Decentralized storage",
        "Wallet & transaction handling",
    ],
    "Artificial Intelligence (AI) Engineer": [
        "Python",
        "ML/DL frameworks (PyTorch/TensorFlow)",
        "Neural network design",
        "Model deployment & MLOps",
        "Data preprocessing & pipelines",
        "Computer vision or NLP (optional)",
        "Responsible AI & ethics",
        "Cloud AI services",
    ],
    "Game Developer": [
        "Game engines (Unity/Unreal/Godot)",
        "C#/C++/game scripting",
        "3D modeling & animation",
        "Physics & game mechanics",
        "Multiplayer networking",
        "Graphics & shaders",
        "Game design & balancing",
        "Optimization & performance",
    ],
    "Human-Computer Interaction (HCI) Specialist": [
        "UX/UI principles",
        "User research & usability testing",
        "Prototyping (Figma/Adobe XD)",
        "Accessibility (WCAG)",
        "Cognitive psychology basics",
        "Interaction design patterns",
        "Heuristic evaluation & A/B testing",
        "User journey mapping",
    ],
}

INTEREST_AREAS = [
    "Building software apps and systems",
    "Analyzing data & creating predictive models",
    "Protecting systems from cyber attacks & ethical hacking",
    "Designing beautiful, functional websites",
    "Managing servers, networks & infrastructure",
    "Deep mathematics & unbreakable encryption",
    "Blockchain, smart contracts & decentralized tech",
    "Artificial Intelligence & machine learning",
    "Creating video games (design + coding)",
    "User experience, interfaces & usability research",
]

BROAD_SKILLS = [
    "Programming (any language)",
    "Mathematics / Statistics",
    "Data handling & analysis",
    "Networking & systems",
    "Design / UI principles",
    "Problem-solving algorithms",
]


@app.post("/assessment/step", response_class=HTMLResponse)
async def assessment_step(request: Request):
    form = await request.form()
    step = int(form.get("current_step", 1))

    if step == 1:
        # Received Part 1 selection → serve Part 2
        selected_path = form.get("selected_path", "")
        return templates.TemplateResponse(request, "partials/step2.html", {
            "selected_path": selected_path,
        })

    elif step == 2:
        # Received Part 2 → serve Part 3 or Part 4
        selected_path = form.get("selected_path", "")
        is_undecided = selected_path == "Not yet known – I want TechPath AI to recommend the best fit for me"
        if is_undecided:
            return templates.TemplateResponse(request, "partials/step3_undecided.html", {
                "selected_path": selected_path,
                "interest_areas": INTEREST_AREAS,
                "broad_skills": BROAD_SKILLS,
            })
        else:
            skills = JOB_SKILLS.get(selected_path, [])
            return templates.TemplateResponse(request, "partials/step4_job.html", {
                "selected_path": selected_path,
                "skills": skills,
            })

    return HTMLResponse("<p>Unknown step</p>", status_code=400)


@app.post("/api/submit-assessment", response_class=HTMLResponse)
async def submit_assessment(
    request: Request,
    session: Session = Depends(get_session),
):
    form = await request.form()
    selected_path = form.get("selected_path", "Unknown")

    # Build raw survey JSON from form
    current_situation = form.getlist("current_situation")
    future_tendency = form.getlist("future_tendency")

    general_profile = {
        "education": form.get("education", ""),
        "experience": form.get("experience", ""),
        "current_situation": current_situation,
        "time_hours_per_week": form.get("time_hours_per_week", ""),
        "schedule_constraints": form.get("schedule_constraints", ""),
        "future_tendency": future_tendency,
        "long_term_vision": form.get("long_term_vision", ""),
    }

    is_undecided = "Not yet known" in selected_path

    if is_undecided:
        interest_scores = {}
        for area in INTEREST_AREAS:
            key = f"interest_{INTEREST_AREAS.index(area)}"
            interest_scores[area] = int(form.get(key, 3))
        broad_skill_scores = {}
        for skill in BROAD_SKILLS:
            key = f"broad_{BROAD_SKILLS.index(skill)}"
            broad_skill_scores[skill] = int(form.get(key, 3))
        survey = {
            "selected_path": selected_path,
            "general_profile": general_profile,
            "undecided_scores": {
                "interest_matching": interest_scores,
                "broad_technical_skills": broad_skill_scores,
                "open_fields": {
                    "existing_skills": form.get("existing_skills", ""),
                    "proud_projects": form.get("proud_projects", ""),
                    "want_to_learn": form.get("want_to_learn", ""),
                }
            }
        }
    else:
        skills = JOB_SKILLS.get(selected_path, [])
        job_ratings = {}
        for i, skill in enumerate(skills):
            job_ratings[skill] = int(form.get(f"skill_{i}", 3))
        survey = {
            "selected_path": selected_path,
            "general_profile": general_profile,
            "job_specific_ratings": job_ratings,
            "job_specific_opens": {
                "additional_skills": form.get("additional_skills", ""),
                "projects": form.get("proud_projects", ""),
                "excited_to_learn": form.get("excited_to_learn", ""),
            }
        }

    # ── Logic Gắn ID Người Dùng ──
    user_id_from_cookie = request.cookies.get("session_token")
    target_user = None
    
    if user_id_from_cookie:
        target_user = session.get(User, int(user_id_from_cookie))
        
    if target_user:
        # Cập nhật thông tin profile từ assessment nếu profile còn trống
        if not target_user.current_status:
            target_user.current_status = general_profile.get("education", "")
        if not target_user.career_goal:
            target_user.career_goal = selected_path
        if not target_user.hours_per_week:
            try:
                # Trích xuất số từ chuỗi ví dụ: "10-15 hours" -> 10
                hours_str = general_profile.get("time_hours_per_week", "")
                if hours_str:
                    import re
                    match = re.search(r'\d+', hours_str)
                    if match:
                        target_user.hours_per_week = int(match.group())
            except:
                pass
        session.add(target_user)
    else:
        # Chỉ tạo User Anonymous nếu chưa đăng nhập
        target_user = User(name="Anonymous", email=f"anon_{uuid.uuid4().hex[:8]}@techpath.ai")
        session.add(target_user)
        session.commit()
        session.refresh(target_user)

    assessment_obj = Assessment(
        user_id=target_user.id,
        session_id=str(uuid.uuid4()),
        selected_path=selected_path,
        raw_survey=json.dumps(survey),
    )
    session.add(assessment_obj)
    session.commit()
    session.refresh(assessment_obj)

    # Call the LLM to generate roadmap and process response
    try:
        roadmap_id = get_model_response(assessment_obj, session)
        return RedirectResponse(url=f"/roadmap/{roadmap_id}", status_code=303)
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate roadmap from AI model.")


# ── Checkpoint Toggle ──────────────────────────────────────────────────────────

@app.post("/api/checkpoint/{checkpoint_id}/toggle", response_class=HTMLResponse)
async def toggle_checkpoint(
    request: Request,
    checkpoint_id: int,
    session: Session = Depends(get_session),
):
    checkpoint = session.get(Checkpoint, checkpoint_id)
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    checkpoint.is_complete = not checkpoint.is_complete
    session.add(checkpoint)

    # Recalculate roadmap progress
    phase = session.get(Phase, checkpoint.phase_id)
    if phase:
        roadmap = session.get(Roadmap, phase.roadmap_id)
        if roadmap:
            all_phases = session.exec(
                select(Phase).where(Phase.roadmap_id == roadmap.id)
            ).all()
            total = 0
            done = 0
            for p in all_phases:
                cps = session.exec(
                    select(Checkpoint).where(Checkpoint.phase_id == p.id)
                ).all()
                total += len(cps)
                done += sum(1 for c in cps if c.is_complete)
            roadmap.overall_progress = round((done / total * 100) if total > 0 else 0, 1)
            session.add(roadmap)

    session.commit()
    session.refresh(checkpoint)

    # Return updated checkpoint button fragment
    return templates.TemplateResponse(request, "partials/checkpoint_btn.html", {
        "checkpoint": checkpoint,
    })


# ── AI Chat (Socratic Tutor) ───────────────────────────────────────────────────

from fastapi.responses import JSONResponse

@app.get("/api/chat/threads")
def get_chat_threads(request: Request, session: Session = Depends(get_session)):
    user_id_str = request.cookies.get("session_token")
    if not user_id_str:
        return {"threads": []}
    
    threads = session.exec(
        select(ChatThread)
        .where(ChatThread.user_id == int(user_id_str))
        .order_by(ChatThread.updated_at.desc())
    ).all()
    
    return {"threads": [
        {"id": t.id, "title": t.title, "updated_at": t.updated_at.isoformat()}
        for t in threads
    ]}

@app.get("/api/chat/thread/{thread_id}")
def get_chat_thread_messages(thread_id: int, session: Session = Depends(get_session)):
    t = session.get(ChatThread, thread_id)
    if not t:
        raise HTTPException(status_code=404, detail="Thread not found")
    msgs = session.exec(select(ChatMessage).where(ChatMessage.thread_id == thread_id).order_by(ChatMessage.created_at)).all()
    return {"thread_id": t.id, "title": t.title, "messages": [{"role": m.role, "content": m.content} for m in msgs]}

@app.post("/api/chat")
async def ai_chat(request: Request, session: Session = Depends(get_session)):
    """
    Socratic AI Tutor endpoint.
    Expects JSON body: { "task": "...", "messages": [...], "want_answer": bool, "thread_id": 123 (optional) }
    Supports: language mirroring, per-user roadmap memory, isolated per-user memory.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    task_context: str = body.get("task", "").strip()
    messages: list = body.get("messages", [])
    want_answer: bool = body.get("want_answer", False)
    thread_id = body.get("thread_id")

    # ── Resolve current user ───────────────────────────────────────────────────
    user_id_str = request.cookies.get("session_token")
    current_user_id: Optional[int] = int(user_id_str) if user_id_str else None
    current_user: Optional[User] = session.get(User, current_user_id) if current_user_id else None

    # ── DB Logic: check or create thread ─────────────────────────────────────
    thread = None
    if thread_id:
        thread = session.get(ChatThread, thread_id)

    if not thread:
        first_human = next((m for m in messages if m.get("role") == "user"), None)
        raw_title = first_human.get("content", "New Chat") if first_human else "New Chat"
        words = raw_title.split()
        title = " ".join(words[:5]) + ("..." if len(words) > 5 else "")
        if task_context:
            title = f"Task: {task_context[:20]}..."

        thread = ChatThread(title=title, user_id=current_user_id)
        session.add(thread)
        session.commit()
        session.refresh(thread)

    thread_id = thread.id

    # Save user's latest message
    if messages and messages[-1].get("role") == "user":
        latest_user_content = messages[-1].get("content", "")
        user_msg = ChatMessage(thread_id=thread_id, role="user", content=latest_user_content)
        session.add(user_msg)
        session.commit()

    # ── Build per-user roadmap context ────────────────────────────────────────
    roadmap_context_section = ""
    user_memory_section = ""

    if current_user_id:
        # Fetch all roadmaps for this user
        user_roadmaps = session.exec(
            select(Roadmap).where(Roadmap.user_id == current_user_id).order_by(Roadmap.created_at.desc())
        ).all()

        if user_roadmaps:
            roadmap_lines = []
            for rm in user_roadmaps:
                roadmap_lines.append(f"\n📋 Roadmap: '{rm.title}' — overall progress: {rm.overall_progress:.1f}%")
                # Fetch phases + checkpoints for this roadmap
                phases = session.exec(
                    select(Phase).where(Phase.roadmap_id == rm.id).order_by(Phase.order_index)
                ).all()
                for ph in phases:
                    cps = session.exec(
                        select(Checkpoint).where(Checkpoint.phase_id == ph.id)
                    ).all()
                    total_cps = len(cps)
                    done_cps = [c for c in cps if c.is_complete]
                    done_count = len(done_cps)
                    status_icon = "✅" if done_count == total_cps and total_cps > 0 else ("🔄" if done_count > 0 else "⏳")
                    roadmap_lines.append(
                        f"  {status_icon} Phase {ph.order_index}: '{ph.name}' — {done_count}/{total_cps} checkpoints completed"
                    )
                    for c in done_cps:
                        roadmap_lines.append(f"      ✔ {c.description}")

            roadmap_context_section = (
                "\n\n=== USER'S LEARNING PROGRESS (from their roadmap) ==="
                + "\n".join(roadmap_lines)
                + "\n\nYou MUST use this data when the user asks about their progress, \"what have I learned\", "
                  "\"where am I\", or similar. Reference specific completed checkpoints by name when relevant."
            )

        # Fetch per-user memory (AI-maintained rolling summary)
        mem = session.exec(select(UserMemory).where(UserMemory.user_id == current_user_id)).first()
        if mem and (mem.summary or mem.key_facts != "[]"):
            try:
                facts = json.loads(mem.key_facts or "[]")
            except Exception:
                facts = []
            facts_text = ""
            if facts:
                facts_text = "\nKey facts I know about this user:\n" + "\n".join(
                    f"  • [{f.get('topic','General')}] {f.get('fact','')}" for f in facts[:20]
                )
            if mem.summary:
                user_memory_section = (
                    "\n\n=== CONVERSATION MEMORY (what I remember about this user) ==="
                    f"\nProfile & Progress Summary: \n{mem.summary}\n{facts_text}"
                    "\n\nCRITICAL MUST-DO:\n"
                    "- Adjust your tone and vocabulary to perfectly match the user's personality and pronouns (cách xưng hô: ví dụ tôi gọi bạn, em gọi anh, v.v.).\n"
                    "- Use their known 'Knowledge Level' and 'Unmarked Progress' to automatically skip basics they already know.\n"
                    "- Pick up right where they left off in their self-directed learning, even if they haven't explicitly marked it 'done' on the roadmap."
                )
            elif facts_text:
                user_memory_section = (
                    "\n\n=== CONVERSATION MEMORY ==="
                    f"{facts_text}"
                    "\n\nUse this to personalize responses."
                )

    # ── Detect language of user's latest message ──────────────────────────────
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    # ── Build system prompt ───────────────────────────────────────────────────
    if task_context:
        task_section = f"""
The learner has clicked on the following learning task from their roadmap:
---
TASK: {task_context}
---

Start by:
1. Briefly introducing what this topic is and why it matters (2-3 sentences).
2. Breaking it down into 3-5 key sub-concepts the learner should understand.
3. Suggesting a realistic study deadline / schedule.
4. Then immediately shift to Socratic mode — ask the learner a probing question to assess their current understanding before diving deeper.
"""
    else:
        task_section = "The learner is asking a general question about their IT career roadmap."

    if want_answer:
        answer_instruction = "The learner has explicitly asked for the answer or full explanation. Provide a clear, complete, and detailed explanation now."
    else:
        answer_instruction = (
            "Use the Socratic method: guide the learner with probing questions, hints, and analogies. "
            "Do NOT give full answers or solutions outright. Instead, ask questions that lead the learner to discover the answer themselves. "
            "Only reveal the full answer if the learner explicitly says they give up, or asks 'tell me the answer', 'show me the solution', 'I want the answer', etc."
        )

    user_name_line = f"The learner's name is: {current_user.name}." if current_user else ""

    system_prompt = f"""You are TechPath AI Tutor — an expert IT mentor who uses the Socratic method to teach.

Your personality:
- Encouraging, patient, and intellectually curious
- You believe learners grow more when they discover answers themselves
- You celebrate small wins and redirect mistakes with questions, not corrections
{user_name_line}

{task_section}

Teaching approach:
{answer_instruction}

Additional rules:
- Keep responses concise and focused (max 4-6 sentences per turn unless giving a full explanation)
- Use simple analogies when introducing new concepts
- If the learner is stuck, give a small hint, then ask another question
- Format any code examples with markdown code blocks
- Always end your response with either a question OR an encouraging next step
- LANGUAGE RULE: Detect the language of the user's most recent message and reply in that SAME language.
  If the user writes in Vietnamese → reply in Vietnamese.
  If the user writes in English → reply in English.
  Do NOT switch languages unless the user switches first.
{roadmap_context_section}
{user_memory_section}
"""

    # ── Build message history ──────────────────────────────────────────────────
    lc_messages = [SystemMessage(content=system_prompt)]
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            lc_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            lc_messages.append(AIMessage(content=content))

    # ── Call LLM ───────────────────────────────────────────────────────────────
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=False)
    try:
        response = llm.invoke(lc_messages)
        ai_reply = response.content

        # Save AI reply to DB
        ai_msg = ChatMessage(thread_id=thread_id, role="assistant", content=ai_reply)
        session.add(ai_msg)
        thread.updated_at = get_vietnam_time()
        session.add(thread)
        session.commit()

        # ── Update per-user memory (background extraction) ────────────────────
        if current_user_id and len(messages) % 4 == 0:  # update every 4 turns
            _update_user_memory(current_user_id, messages, ai_reply, session)

        return JSONResponse({"reply": ai_reply, "thread_id": thread_id})
    except Exception as e:
        print(f"AI Chat error: {e}")
        raise HTTPException(status_code=500, detail="AI service unavailable. Please try again.")


def _update_user_memory(user_id: int, messages: list, latest_reply: str, session: Session):
    """Extract key facts from conversation and update UserMemory for this user.
    Uses a lightweight LLM call to summarise only new information."""
    try:
        # Fetch or create memory record for this user
        mem = session.exec(select(UserMemory).where(UserMemory.user_id == user_id)).first()
        if not mem:
            mem = UserMemory(user_id=user_id, summary="", key_facts="[]")
            session.add(mem)
            session.commit()
            session.refresh(mem)

        # Build a condensed conversation snapshot (last 10 turns)
        recent = messages[-10:]
        conv_text = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in recent
        ) + f"\nASSISTANT: {latest_reply}"

        extraction_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        extraction_prompt = f"""We are updating the persistent memory profile of the user based on their latest conversation.

Current Profile Summary:
{mem.summary}

Recent Conversation:
{conv_text}

Task: Update the user's profile summary based on the new conversation snippet.
1. Extract NEW factual statements (e.g. name, specific interests, tech stacks) as a list of dicts.
2. Provide an UPDATED comprehensive profile summary capturing:
   - The user's personality and how they address themselves/you (cách xưng hô: ví dụ dùng "tôi", "mình", "em", "anh", "bạn", v.v.).
   - What knowledge topics they have asked about and their CURRENT knowledge level.
   - Any NEW topics they have learned or demonstrated understanding of (unmarked progress) in this chat, even if they didn't click "mark done".

Return ONLY valid JSON with the following structure:
{{
   "updated_summary": "Paragraph summarizing personality, pronouns, knowledge level, and recent unmarked progress. Combine old and new info.",
   "new_facts": [
      {{"topic": "...", "fact": "..."}}
   ]
}}
"""
        extraction_response = extraction_llm.invoke([HumanMessage(content=extraction_prompt)])
        raw_json = extraction_response.content.strip()
        # Strip markdown fences if present
        if raw_json.startswith("```"):
            if "```json" in raw_json:
                raw_json = raw_json.split("```json", 1)[-1].rsplit("```", 1)[0].strip()
            else:
                raw_json = raw_json.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        
        parsed = json.loads(raw_json)
        updated_summary = parsed.get("updated_summary", "")
        new_facts = parsed.get("new_facts", [])
        if not isinstance(new_facts, list):
            new_facts = []

        existing_facts: list = json.loads(mem.key_facts or "[]")
        # Merge: add new facts, avoid near-duplicates (simple text check), cap at 30
        existing_texts = {f.get("fact", "").lower() for f in existing_facts}
        for nf in new_facts:
            if nf.get("fact", "").lower() not in existing_texts:
                existing_facts.append(nf)
                existing_texts.add(nf.get("fact", "").lower())
        existing_facts = existing_facts[-30:]  # keep latest 30

        if updated_summary:
            mem.summary = updated_summary
        mem.key_facts = json.dumps(existing_facts, ensure_ascii=False)
        mem.updated_at = get_vietnam_time()
        session.add(mem)
        session.commit()
    except Exception as ex:
        print(f"Memory update error (non-critical): {ex}")

