import sqlite3
import os

DB_PATH = "techpath.db"

def reset_database():
    print(f"--- Đang dọn dẹp dữ liệu trong {DB_PATH} ---")
    if not os.path.exists(DB_PATH):
        print("Không tìm thấy file database.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Hiển thị các bảng hiện có
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if row[0] != 'sqlite_sequence']
        
        print(f"Các bảng sẽ được xóa dữ liệu: {tables}")
        
        # Xóa dữ liệu từng bảng
        for table in tables:
            print(f"Đang xóa dữ liệu bảng: {table}...")
            cursor.execute(f"DELETE FROM {table}")
        
        # Reset các auto-increment counters
    #    ursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        print("--- ĐÃ XÓA TOÀN BỘ DỮ LIỆU THÀNH CÔNG ---")
        print("Bây giờ bạn có thể test đăng ký/login lại từ đầu.")
    except Exception as e:
        print(f"Lỗi khi xóa dữ liệu: {e}")

if __name__ == "__main__":
    confirm = input("CẢNH BÁO: Hành động này sẽ xóa TOÀN BỘ người dùng và dữ liệu trong DB. Bạn có chắc chắn? (y/n): ")
    if confirm.lower() == 'y':
        reset_database()
    else:
        print("Hủy bỏ thao tác.")
