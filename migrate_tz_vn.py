"""
One-shot migration: shift all existing timestamps stored as UTC by +7 hours,
so they reflect Vietnam local time after switching get_vietnam_time() to naive.

Run ONCE. Re-running will double-shift -> safeguard via env flag.
Usage:
  CONFIRM_TZ_MIGRATION=1 python migrate_tz_vn.py
"""
import os
import sys
from sqlalchemy import text
from sqlmodel import Session
from database import engine

if os.getenv("CONFIRM_TZ_MIGRATION") != "1":
    print("Refusing to run without CONFIRM_TZ_MIGRATION=1 (prevents double-shift).")
    sys.exit(1)

# (table_name, [datetime columns])
TARGETS = [
    ('"user"', ['created_at']),
    ('passwordresettoken', ['created_at', 'expires_at']),
    ('assessment', ['created_at']),
    ('matchresult', ['created_at']),
    ('roadmap', ['created_at']),
    ('chatthread', ['created_at', 'updated_at']),
    ('chatmessage', ['created_at']),
    ('usermemory', ['updated_at']),
]

with Session(engine) as s:
    for table, cols in TARGETS:
        for col in cols:
            sql = f"UPDATE {table} SET {col} = {col} + INTERVAL '7 hours' WHERE {col} IS NOT NULL"
            result = s.exec(text(sql))
            print(f"  {table}.{col}: shifted {result.rowcount} rows")
    s.commit()

print("Done. All existing timestamps shifted +7h to Vietnam local time.")
