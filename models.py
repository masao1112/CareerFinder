import json
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Column, Index
import sqlalchemy as sa


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Assessment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    session_id: str = Field(index=True)
    selected_path: str
    raw_survey: str  # JSON string
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MatchResult(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    assessment_id: Optional[int] = Field(default=None, foreign_key="assessment.id")
    top_matches: str  # JSON string: [{"path": "...", "score": 0.92}, ...]
    recommended_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Roadmap(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)
    assessment_id: Optional[int] = Field(default=None, foreign_key="assessment.id")
    title: str
    overall_progress: float = Field(default=0.0)  # 0.0 – 100.0
    created_at: datetime = Field(default_factory=datetime.utcnow)


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
