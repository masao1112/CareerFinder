from sqlmodel import Session, select
from models import Roadmap, User, Phase, Checkpoint, ProjectIdea, Resource, Assessment, MatchResult
import json
import os
from pydantic import BaseModel, Field
from typing import List
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_classic import hub

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
    
    # 1. Search Agent to gather information
    search = DuckDuckGoSearchRun()
    tools = [search]
    
    # Using a generic prompt for tool-calling agent
    prompt = hub.pull("hwchase17/openai-tools-agent")
    agent = create_openai_tools_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    
    selected_path = user_assessment.selected_path
    search_query = f"detailed learning roadmap and best resources for {selected_path} career path in 2024-2025"
    
    print(f"Researching: {search_query}")
    research_results = agent_executor.invoke({
        "input": f"Search for the latest, most detailed technical roadmap, essential skills, and high-quality learning resources for a career in {selected_path}. Focus on specific tools, frameworks, and real-world project ideas. Return a summary of your findings."
    })
    
    information_gathered = research_results["output"]
    
    # 2. Generate structured output using gathered info
    structured_llm = llm.with_structured_output(RoadmapOutput)
    
    prompt_text = f"""
    You are an expert career counselor and technical mentor. 
    Analyze the following user assessment and the researched information to create a comprehensive tech career roadmap.
    
    User Assessment Data:
    {user_assessment.raw_survey}
    
    Selected Path: {selected_path}
    
    Researched Information:
    {information_gathered}
    
    Your task:
    1. Evaluate the user's fit for ALL 10 of these tech careers and provide a score (0-100) for each:
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
    2. Recommend the best path (which should be one of the 10).
    3. Create a VERY DETAILED, personalized technical roadmap consisting of at least 5-6 progressive phases.
       For each phase, you MUST provide:
       - name: A clear, professional title for the phase.
       - description: A detailed overview (3-4 sentences) including the phase's focus, estimated time (weeks/months), and difficulty level.
       - checkpoints: At least 5 granular milestones. Each milestone should be a specific skill or concept (e.g., "Mastering CSS Grid and Flexbox", "Implementing JWT Authentication").
       - projects: 2-3 practical project ideas with titles and 2-3 sentence implementation guides.
       - resources: 3-5 high-quality, real resources. Provide the title, verified URL, and specify if it's a course, article, or documentation.
    
    Ensure the roadmap is logically ordered and targets the user's specific background and goals from the assessment.
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