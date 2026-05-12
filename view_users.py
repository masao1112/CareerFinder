from sqlmodel import Session, select, create_engine
from models import User, Roadmap
import os

# Kết nối DB
sqlite_url = "sqlite:///techpath.db"
engine = create_engine(sqlite_url)

def view_data():
    with Session(engine) as session:
        print("\n" + "="*30)
        print("📊 DANH SÁCH NGƯỜI DÙNG (USER)")
        print("="*30)
        users = session.exec(select(User)).all()
        # Header
        header = f"{'ID':<3} | {'Tên':<20} | {'Email':<30} | {'Ngày tạo':<20} | {'Mục tiêu':<20}"
        print(header)
        print("-" * len(header))
        for u in users:
            created = u.created_at.strftime('%Y-%m-%d %H:%M') if u.created_at else "N/A"
            goal = u.career_goal if u.career_goal else "Chưa có"
            print(f"{u.id:<3} | {u.name:<20} | {u.email:<30} | {created:<20} | {goal:<20}")

        print("\n" + "="*30)
        print("🗺️ DANH SÁCH ROADMAP")
        print("="*30)
        roadmaps = session.exec(select(Roadmap)).all()
        header_rm = f"{'ID':<3} | {'UserID':<7} | {'Tiến độ':<8} | {'Tiêu đề lộ trình'}"
        print(header_rm)
        print("-" * len(header_rm))
        for r in roadmaps:
            print(f"{r.id:<3} | {r.user_id:<7} | {r.overall_progress:<8}% | {r.title}")

if __name__ == "__main__":
    if os.path.exists("techpath.db"):
        view_data()
    else:
        print("Không tìm thấy file techpath.db!")
