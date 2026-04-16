from sqlmodel import Session, select
from models import Roadmap, User, Phase, Checkpoint, ProjectIdea, Resource, Assessment, MatchResult
import json
import os
from pydantic import BaseModel, Field
from typing import List
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

class JobMatch(BaseModel):
    path: str
    score: int = Field(description="Score from 0 to 100")

class StructuredResource(BaseModel):
    title: str
    url: str
    is_free: bool
    type: str = Field(description="article, video, course, book, or tool")

class StructuredProject(BaseModel):
    title: str
    description: str

class StructuredCheckpoint(BaseModel):
    description: str

class StructuredPhase(BaseModel):
    name: str
    description: str
    checkpoints: List[StructuredCheckpoint]
    projects: List[StructuredProject]
    resources: List[StructuredResource]

class RoadmapOutput(BaseModel):
    recommended_path: str
    job_scores: List[JobMatch] = Field(description="Evaluation scores for ALL 10 predefined career paths, from 0 to 100")
    title: str = Field(description="Title of the personalized roadmap")
    phases: List[StructuredPhase] = Field(description="List of phases in the roadmap")

# Get roadmap data
def get_roadmap_data(roadmap_id: int, session: Session):
    roadmap = session.get(Roadmap, roadmap_id)
    if not roadmap:
        return None, None, None, None

    user = session.get(User, roadmap.user_id)
    phases = session.exec(
        select(Phase).where(Phase.roadmap_id == roadmap_id).order_by(Phase.order_index)
    ).all()

    phase_data = []
    for phase in phases:
        checkpoints = session.exec(
            select(Checkpoint).where(Checkpoint.phase_id == phase.id)
        ).all()
        projects = session.exec(
            select(ProjectIdea).where(ProjectIdea.phase_id == phase.id)
        ).all()
        resources = session.exec(
            select(Resource).where(Resource.phase_id == phase.id)
        ).all()
        phase_data.append({
            "phase": phase,
            "checkpoints": checkpoints,
            "projects": projects,
            "resources": resources,
        })

    return roadmap, user, phase_data

# Get model response
def get_model_response(user_assessment: Assessment, session: Session):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)
    structured_llm = llm.with_structured_output(RoadmapOutput)
    
    prompt_text = f"""
    You are an elite expert career counselor, senior technical mentor, and curriculum designer. 
    Analyze the following user assessment for a tech career in extensive detail:
    {user_assessment.raw_survey}
    
    The user is interested in or selected: {user_assessment.selected_path}
    
    Your task:
    1. Evaluate the user's fit for ALL 10 of these tech careers and provide a score (0-100) for each based on their assessment:
       - Software Engineer
       - Data Scientist
       - Cybersecurity Engineer
       - Web Developer
       - Systems Administrator
       - Cryptographer
       - Blockchain Developer
       - Artificial Intelligence (AI) Engineer
       - Game Developer
       - Human-Computer Interaction (HCI) Specialist
    2. Recommend the best path (which should be one of the 10) and generate an extremely detailed, exhaustive, and personalized technical roadmap.
    3. The roadmap MUST contain multiple comprehensive phases (at least 4-6 phases).
    4. For EACH phase, you MUST provide:
       - An in-depth, long description (at least 3-4 sentences) explaining exactly what the user will learn and why it is important.
       - Detailed checkpoints (milestones) with elaborate descriptions outlining specific skills to master. Produce at least 5-8 checkpoints per phase.
       - Highly descriptive project ideas. Each project description should act as a mini-spec, detailing the problem statement, expected features, and technologies to use. Produce at least 2-3 complex projects per phase.
       - An exhaustive list of resources (at least 4-6 resources per phase) including specific URLs (or realistic high-quality placeholders), mixed with courses, books, and articles.
       
    CRITICAL INSTRUCTION: Make the output as long, verbose, descriptive, and actionable as possible. Do not output brief or high-level summaries. Give concrete examples, detailed advice, and extensive technical requirements for every single item.
    """
    
    response: RoadmapOutput = structured_llm.invoke(prompt_text)
    
    match = MatchResult(
        assessment_id=user_assessment.id,
        top_matches=json.dumps([{"path": j.path, "score": j.score} for j in response.job_scores]),
        recommended_path=response.recommended_path,
    )
    session.add(match)
    session.commit()
    
    roadmap = Roadmap(
        user_id=user_assessment.user_id,
        assessment_id=user_assessment.id,
        title=response.title,
        overall_progress=0.0
    )
    session.add(roadmap)
    session.commit()
    session.refresh(roadmap)
    
    for i, phase_data in enumerate(response.phases):
        phase = Phase(
            roadmap_id=roadmap.id,
            name=phase_data.name,
            order_index=i + 1,
            description=phase_data.description
        )
        session.add(phase)
        session.commit()
        session.refresh(phase)
        
        for cp in phase_data.checkpoints:
            checkpoint = Checkpoint(
                phase_id=phase.id,
                description=cp.description
            )
            session.add(checkpoint)
            
        for proj in phase_data.projects:
            project = ProjectIdea(
                phase_id=phase.id,
                title=proj.title,
                description=proj.description
            )
            session.add(project)
            
        for res in phase_data.resources:
            resource = Resource(
                phase_id=phase.id,
                title=res.title,
                url=res.url,
                is_free=res.is_free,
                type=res.type
            )
            session.add(resource)
            
    session.commit()
    return roadmap.id