import json
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlmodel import SQLModel, Field, Column, Index
import sqlalchemy as sa


def get_vietnam_time():
    return datetime.now(timezone(timedelta(hours=7)))


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True)
    password_hash: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=get_vietnam_time)
    
    # Career-focused fields
    current_status: Optional[str] = Field(default=None)  # e.g., Student, Fresher, Transitioner
    primary_skills: Optional[str] = Field(default=None)  # e.g., Python, SQL, JS
    career_goal: Optional[str] = Field(default=None)     # e.g., Senior Data Scientist
    hours_per_week: Optional[int] = Field(default=None)  # e.g., 10, 20



class PasswordResetToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    otp_code: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=get_vietnam_time)


class Assessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    session_id: str = Field(index=True)
    selected_path: str
    raw_survey: str  # JSON string
    created_at: datetime = Field(default_factory=get_vietnam_time)


class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_id: Optional[int] = Field(default=None, foreign_key="assessment.id")
    top_matches: str  # JSON string: [{"path": "...", "score": 0.92}, ...]
    recommended_path: str
    created_at: datetime = Field(default_factory=get_vietnam_time)


class Roadmap(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    assessment_id: Optional[int] = Field(default=None, foreign_key="assessment.id")
    title: str
    overall_progress: float = Field(default=0.0)  # 0.0 – 100.0
    created_at: datetime = Field(default_factory=get_vietnam_time)


class Phase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    roadmap_id: Optional[int] = Field(default=None, foreign_key="roadmap.id")
    name: str
    order_index: int
    description: str = ""


class Checkpoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")
    description: str
    is_complete: bool = False


class ProjectIdea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")
    title: str
    description: str = ""


class Resource(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    phase_id: Optional[int] = Field(default=None, foreign_key="phase.id")
    title: str
    url: str
    is_free: bool = True
    type: str = "article"  # article | video | course | book | tool


class ChatThread(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    title: str = Field(default="New Chat")
    created_at: datetime = Field(default_factory=get_vietnam_time)
    updated_at: datetime = Field(default_factory=get_vietnam_time)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    thread_id: int = Field(foreign_key="chatthread.id", index=True)
    role: str  # "user", "assistant", or "system"
    content: str
    created_at: datetime = Field(default_factory=get_vietnam_time)
