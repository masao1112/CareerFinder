"""
main.py – TechPath AI FastAPI application
"""
import json
import uuid
from typing import Optional, List
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from database import create_db_and_tables, get_session
from models import (
    User, Assessment, MatchResult, Roadmap,
    Phase, Checkpoint, ProjectIdea, Resource,
)
from helpers import get_roadmap_data, get_model_response

app = FastAPI(title="TechPath AI")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ── Pages ──────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/assessment", response_class=HTMLResponse)
async def assessment(request: Request):
    return templates.TemplateResponse("assessment.html", {
        "request": request,
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
            top_matches = json.loads(match_result.top_matches)

    return templates.TemplateResponse("roadmap.html", {
        "request": request,
        "roadmap": roadmap,
        "user": user,
        "phase_data": phase_data,
        "top_matches": top_matches,
        "match_result": match_result,
    })


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
        return templates.TemplateResponse("partials/step2.html", {
            "request": request,
            "selected_path": selected_path,
        })

    elif step == 2:
        # Received Part 2 → serve Part 3 or Part 4
        selected_path = form.get("selected_path", "")
        is_undecided = selected_path == "Not yet known – I want TechPath AI to recommend the best fit for me"
        if is_undecided:
            return templates.TemplateResponse("partials/step3_undecided.html", {
                "request": request,
                "selected_path": selected_path,
                "interest_areas": INTEREST_AREAS,
                "broad_skills": BROAD_SKILLS,
            })
        else:
            skills = JOB_SKILLS.get(selected_path, [])
            return templates.TemplateResponse("partials/step4_job.html", {
                "request": request,
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

    # Create anonymous user if not logged in
    anon_user = User(name="Anonymous", email=f"anon_{uuid.uuid4().hex[:8]}@techpath.ai")
    session.add(anon_user)
    session.commit()
    session.refresh(anon_user)

    assessment_obj = Assessment(
        user_id=anon_user.id,
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
    return templates.TemplateResponse("partials/checkpoint_btn.html", {
        "request": request,
        "checkpoint": checkpoint,
    })
