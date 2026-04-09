"""
seed.py – run once to populate techpath.db with 3 mock users.
Usage: python seed.py
"""
import json
import sys
from passlib.context import CryptContext
from database import create_db_and_tables, engine
from models import (
    User, Assessment, MatchResult, Roadmap,
    Phase, Checkpoint, ProjectIdea, Resource,
)
from sqlmodel import Session


def seed():
    create_db_and_tables()

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_pwd = pwd_context.hash("password123")

    with Session(engine) as session:
        # ── User 1: Alice – Software Engineer ──────────────────────────────
        alice = User(name="Alice Johnson", email="alice@example.com", password_hash=hashed_pwd)
        session.add(alice)
        session.commit()
        session.refresh(alice)

        alice_survey = {
            "selected_path": "Software Engineer",
            "general_profile": {
                "education": "Bachelor's in CS or related",
                "experience": "1–2 years",
                "current_situation": ["Student", "Looking for first role"],
                "time_hours_per_week": "15–20 hours",
                "schedule_constraints": "Evenings free after 7 pm, weekends fully available.",
                "future_tendency": ["High salary & stability", "Solo deep technical work", "Entrepreneurship / building products"],
                "long_term_vision": "Lead engineer at a product startup, building scalable systems."
            },
            "job_specific_ratings": {
                "Programming (Python/Java/C++/etc.)": 3,
                "Algorithms & data structures": 2,
                "Git & version control": 3,
                "Testing & debugging": 2,
                "Cloud platforms (AWS/Azure)": 1,
                "Databases (SQL/NoSQL)": 2,
                "Clean code & design patterns": 2,
                "APIs & microservices": 1,
            },
            "job_specific_opens": {
                "additional_skills": "Python basics, some HTML/CSS",
                "projects": "Built a to-do app in Flask for a class project.",
                "excited_to_learn": "System design and distributed systems"
            }
        }
        alice_assessment = Assessment(
            user_id=alice.id,
            session_id="sess-alice-001",
            selected_path="Software Engineer",
            raw_survey=json.dumps(alice_survey),
        )
        session.add(alice_assessment)
        session.commit()
        session.refresh(alice_assessment)

        alice_match = MatchResult(
            assessment_id=alice_assessment.id,
            top_matches=json.dumps([
                {"path": "Software Engineer", "score": 92},
                {"path": "Web Developer", "score": 74},
                {"path": "Data Scientist", "score": 61},
            ]),
            recommended_path="Software Engineer",
        )
        session.add(alice_match)

        alice_roadmap = Roadmap(
            user_id=alice.id,
            assessment_id=alice_assessment.id,
            title="Your 9-Month Software Engineer Roadmap",
            overall_progress=14.0,
        )
        session.add(alice_roadmap)
        session.commit()
        session.refresh(alice_roadmap)

        def add_phase(name, order, desc, roadmap_id):
            p = Phase(roadmap_id=roadmap_id, name=name, order_index=order, description=desc)
            session.add(p)
            session.commit()
            session.refresh(p)
            return p

        def add_checkpoint(phase_id, desc, complete=False):
            c = Checkpoint(phase_id=phase_id, description=desc, is_complete=complete)
            session.add(c)

        def add_project(phase_id, title, desc):
            p = ProjectIdea(phase_id=phase_id, title=title, description=desc)
            session.add(p)

        def add_resource(phase_id, title, url, is_free=True, rtype="course"):
            r = Resource(phase_id=phase_id, title=title, url=url, is_free=is_free, type=rtype)
            session.add(r)

        # Alice phases
        p1 = add_phase("Phase 1: Foundations", 1,
                        "Master programming fundamentals, Git, and basic algorithms.",
                        alice_roadmap.id)
        add_checkpoint(p1.id, "Complete Python crash course", complete=True)
        add_checkpoint(p1.id, "Learn Git & GitHub (branching, PRs)", complete=True)
        add_checkpoint(p1.id, "Solve 20 easy LeetCode problems")
        add_project(p1.id, "CLI Task Manager",
                    "Build a command-line task manager in Python with file persistence.")
        add_resource(p1.id, "CS50P – Python (Harvard)", "https://cs50.harvard.edu/python/", is_free=True, rtype="course")
        add_resource(p1.id, "Git & GitHub Crash Course", "https://www.youtube.com/watch?v=RGOj5yH7evk", is_free=True, rtype="video")
        add_resource(p1.id, "LeetCode Easy Track", "https://leetcode.com/studyplan/leetcode-75/", is_free=True, rtype="tool")

        p2 = add_phase("Phase 2: Core Skills", 2,
                        "Data structures, algorithms, SQL, and REST APIs.",
                        alice_roadmap.id)
        add_checkpoint(p2.id, "Study arrays, linked lists, stacks, queues")
        add_checkpoint(p2.id, "Build a CRUD REST API with FastAPI")
        add_checkpoint(p2.id, "Learn SQL basics and database design")
        add_project(p2.id, "Expense Tracker API",
                    "REST API with FastAPI + SQLite tracking expenses by category. Include JWT auth.")
        add_resource(p2.id, "Algorithms Specialization – Stanford", "https://www.coursera.org/specializations/algorithms", is_free=False, rtype="course")
        add_resource(p2.id, "FastAPI Official Tutorial", "https://fastapi.tiangolo.com/tutorial/", is_free=True, rtype="article")
        add_resource(p2.id, "SQLZoo – Interactive SQL", "https://sqlzoo.net/", is_free=True, rtype="tool")

        p3 = add_phase("Phase 3: Tools & Frameworks", 3,
                        "Docker, cloud basics, testing, and clean architecture.",
                        alice_roadmap.id)
        add_checkpoint(p3.id, "Containerize an app with Docker")
        add_checkpoint(p3.id, "Deploy to AWS EC2 or Render")
        add_checkpoint(p3.id, "Write unit & integration tests with pytest")
        add_project(p3.id, "Dockerised Microservice",
                    "Split the Expense Tracker into two services (auth + data), orchestrate with Docker Compose.")
        add_resource(p3.id, "Docker for Beginners", "https://docker-curriculum.com/", is_free=True, rtype="article")
        add_resource(p3.id, "AWS Free Tier Getting Started", "https://aws.amazon.com/getting-started/", is_free=True, rtype="article")
        add_resource(p3.id, "Udemy: Docker & Kubernetes", "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/", is_free=False, rtype="course")

        p4 = add_phase("Phase 4: Projects & Portfolio", 4,
                        "Ship two full projects and polish your GitHub portfolio.",
                        alice_roadmap.id)
        add_checkpoint(p4.id, "Ship capstone project to production")
        add_checkpoint(p4.id, "Write README and architecture docs")
        add_checkpoint(p4.id, "Contribute a small PR to an open-source repo")
        add_project(p4.id, "Full-Stack SaaS MVP",
                    "Build a subscription-based note-taking tool with FastAPI backend, HTMX frontend, Stripe integration.")
        add_resource(p4.id, "GitHub Portfolio Guide", "https://github.com/durgeshsamariya/awesome-github-profile-readme-templates", is_free=True, rtype="article")
        add_resource(p4.id, "Stripe Docs – Payments", "https://stripe.com/docs/payments/quickstart", is_free=True, rtype="article")
        session.commit()

        # ── User 2: Bob – Data Scientist ────────────────────────────────────
        bob = User(name="Bob Martinez", email="bob@example.com", password_hash=hashed_pwd)
        session.add(bob)
        session.commit()
        session.refresh(bob)

        bob_survey = {
            "selected_path": "Data Scientist",
            "general_profile": {
                "education": "Master's / PhD",
                "experience": "3–5 years",
                "current_situation": ["Full-time job", "Career switcher"],
                "time_hours_per_week": "10–15 hours",
                "schedule_constraints": "Weekdays limited, Saturday mornings free.",
                "future_tendency": ["High salary & stability", "Remote-first lifestyle", "Solo deep technical work"],
                "long_term_vision": "Principal Data Scientist at a tech company working on NLP products."
            },
            "job_specific_ratings": {
                "Python or R": 4,
                "Statistics & probability": 4,
                "Machine-learning algorithms": 3,
                "Data visualization (Tableau/Matplotlib)": 3,
                "SQL & big-data tools": 3,
                "Model training & evaluation": 3,
                "Data cleaning & feature engineering": 4,
                "Ethics in data science": 2,
            },
            "job_specific_opens": {
                "additional_skills": "Pandas, NumPy, R, Excel",
                "projects": "Built churn prediction model for telecom client.",
                "excited_to_learn": "Deep learning and NLP with transformers"
            }
        }
        bob_assessment = Assessment(
            user_id=bob.id,
            session_id="sess-bob-001",
            selected_path="Data Scientist",
            raw_survey=json.dumps(bob_survey),
        )
        session.add(bob_assessment)
        session.commit()
        session.refresh(bob_assessment)

        bob_match = MatchResult(
            assessment_id=bob_assessment.id,
            top_matches=json.dumps([
                {"path": "Data Scientist", "score": 95},
                {"path": "Artificial Intelligence (AI) Engineer", "score": 81},
                {"path": "Software Engineer", "score": 58},
            ]),
            recommended_path="Data Scientist",
        )
        session.add(bob_match)

        bob_roadmap = Roadmap(
            user_id=bob.id,
            assessment_id=bob_assessment.id,
            title="Your 6-Month Data Scientist Roadmap",
            overall_progress=40.0,
        )
        session.add(bob_roadmap)
        session.commit()
        session.refresh(bob_roadmap)

        bp1 = add_phase("Phase 1: Foundations", 1,
                         "Solidify stats, Python data stack, and SQL.", bob_roadmap.id)
        add_checkpoint(bp1.id, "Review probability & Bayesian reasoning", complete=True)
        add_checkpoint(bp1.id, "Master Pandas & NumPy", complete=True)
        add_checkpoint(bp1.id, "Write 5 exploratory data analyses (EDA)")
        add_project(bp1.id, "EDA on Open Dataset",
                    "Pick a Kaggle dataset; produce a full EDA notebook with Matplotlib/Seaborn. Publish on Kaggle.")
        add_resource(bp1.id, "Kaggle – Pandas Course", "https://www.kaggle.com/learn/pandas", is_free=True, rtype="course")
        add_resource(bp1.id, "StatQuest YouTube", "https://www.youtube.com/@statquest", is_free=True, rtype="video")

        bp2 = add_phase("Phase 2: Core Skills", 2,
                         "Classical ML, model evaluation, feature engineering.", bob_roadmap.id)
        add_checkpoint(bp2.id, "Implement linear & logistic regression from scratch", complete=True)
        add_checkpoint(bp2.id, "Complete scikit-learn ML pipeline project")
        add_checkpoint(bp2.id, "Enter a Kaggle competition (top 40%)")
        add_project(bp2.id, "Customer Churn Predictor",
                    "End-to-end pipeline with feature engineering, cross-validation, model comparison, and a simple Flask API.")
        add_resource(bp2.id, "Hands-On ML – O'Reilly", "https://www.oreilly.com/library/view/hands-on-machine-learning/9781492032632/", is_free=False, rtype="book")
        add_resource(bp2.id, "scikit-learn User Guide", "https://scikit-learn.org/stable/user_guide.html", is_free=True, rtype="article")

        bp3 = add_phase("Phase 3: Deep Learning & NLP", 3,
                         "PyTorch fundamentals, transformers, and NLP pipelines.", bob_roadmap.id)
        add_checkpoint(bp3.id, "Complete fast.ai deep learning course")
        add_checkpoint(bp3.id, "Fine-tune a BERT model on custom text")
        add_project(bp3.id, "Sentiment Analyser API",
                    "Fine-tune DistilBERT on product reviews; serve predictions via FastAPI. Deploy on HuggingFace Spaces.")
        add_resource(bp3.id, "fast.ai – Practical Deep Learning", "https://course.fast.ai/", is_free=True, rtype="course")
        add_resource(bp3.id, "HuggingFace NLP Course", "https://huggingface.co/learn/nlp-course/", is_free=True, rtype="course")
        add_resource(bp3.id, "Udemy: PyTorch for Deep Learning", "https://www.udemy.com/course/pytorch-for-deep-learning-and-computer-vision/", is_free=False, rtype="course")
        session.commit()

        # ── User 3: Carol – Undecided → AI Engineer ──────────────────────────
        carol = User(name="Carol Chen", email="carol@example.com", password_hash=hashed_pwd)
        session.add(carol)
        session.commit()
        session.refresh(carol)

        carol_survey = {
            "selected_path": "Not yet known – I want TechPath AI to recommend the best fit for me",
            "general_profile": {
                "education": "Associate's / Bootcamp",
                "experience": "< 1 year",
                "current_situation": ["Student", "Looking for first role"],
                "time_hours_per_week": "20+ hours",
                "schedule_constraints": "Full-time student until June, then completely free.",
                "future_tendency": ["Creative / innovative projects", "Entrepreneurship / building products", "Helping people / social impact"],
                "long_term_vision": "Build AI tools that help underserved communities access quality education."
            },
            "undecided_scores": {
                "interest_matching": {
                    "Building software apps and systems": 4,
                    "Analyzing data & creating predictive models": 5,
                    "Protecting systems from cyber attacks & ethical hacking": 2,
                    "Designing beautiful, functional websites": 3,
                    "Managing servers, networks & infrastructure": 1,
                    "Deep mathematics & unbreakable encryption": 3,
                    "Blockchain, smart contracts & decentralized tech": 2,
                    "Artificial Intelligence & machine learning": 5,
                    "Creating video games (design + coding)": 2,
                    "User experience, interfaces & usability research": 3,
                },
                "broad_technical_skills": {
                    "Programming (any language)": 3,
                    "Mathematics / Statistics": 3,
                    "Data handling & analysis": 2,
                    "Networking & systems": 1,
                    "Design / UI principles": 2,
                    "Problem-solving algorithms": 3,
                },
                "open_fields": {
                    "existing_skills": "Python, basic ML from bootcamp, some Jupyter notebooks",
                    "proud_projects": "Built a TensorFlow image classifier for a class project.",
                    "want_to_learn": "Reinforcement learning and building real AI products"
                }
            }
        }
        carol_assessment = Assessment(
            user_id=carol.id,
            session_id="sess-carol-001",
            selected_path="Not yet known",
            raw_survey=json.dumps(carol_survey),
        )
        session.add(carol_assessment)
        session.commit()
        session.refresh(carol_assessment)

        carol_match = MatchResult(
            assessment_id=carol_assessment.id,
            top_matches=json.dumps([
                {"path": "Artificial Intelligence (AI) Engineer", "score": 94},
                {"path": "Data Scientist", "score": 83},
                {"path": "Software Engineer", "score": 67},
            ]),
            recommended_path="Artificial Intelligence (AI) Engineer",
        )
        session.add(carol_match)

        carol_roadmap = Roadmap(
            user_id=carol.id,
            assessment_id=carol_assessment.id,
            title="Your 12-Month AI Engineer Roadmap",
            overall_progress=5.0,
        )
        session.add(carol_roadmap)
        session.commit()
        session.refresh(carol_roadmap)

        cp1 = add_phase("Phase 1: Foundations", 1,
                         "Python mastery, mathematics for ML, and your first neural network.", carol_roadmap.id)
        add_checkpoint(cp1.id, "Complete Python for Data Science track", complete=True)
        add_checkpoint(cp1.id, "Review linear algebra (vectors, matrices, eigenvalues)")
        add_checkpoint(cp1.id, "Implement a neural network from scratch with NumPy")
        add_project(cp1.id, "Handwritten Digit Classifier",
                    "Train a neural net from scratch on MNIST. Achieve > 97% accuracy. Share notebook on GitHub.")
        add_resource(cp1.id, "3Blue1Brown – Neural Networks", "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi", is_free=True, rtype="video")
        add_resource(cp1.id, "fast.ai Part 1", "https://course.fast.ai/", is_free=True, rtype="course")
        add_resource(cp1.id, "Mathematics for Machine Learning – Coursera", "https://www.coursera.org/specializations/mathematics-machine-learning", is_free=False, rtype="course")

        cp2 = add_phase("Phase 2: Core Skills", 2,
                         "PyTorch, model training pipelines, and applied ML projects.", carol_roadmap.id)
        add_checkpoint(cp2.id, "Build 3 ML projects end-to-end in PyTorch")
        add_checkpoint(cp2.id, "Learn MLOps basics – experiment tracking with MLflow")
        add_project(cp2.id, "Real-Time Object Detection App",
                    "Fine-tune YOLOv8 on a custom dataset; wrap in a Streamlit app. Deploy on HuggingFace Spaces.")
        add_resource(cp2.id, "PyTorch Official Tutorials", "https://pytorch.org/tutorials/", is_free=True, rtype="article")
        add_resource(cp2.id, "Practical MLOps – O'Reilly", "https://www.oreilly.com/library/view/practical-mlops/9781098103002/", is_free=False, rtype="book")

        cp3 = add_phase("Phase 3: Specialisation – LLMs & Agents", 3,
                         "Large language models, prompt engineering, RAG, and AI agent frameworks.", carol_roadmap.id)
        add_checkpoint(cp3.id, "Complete LangChain crash course")
        add_checkpoint(cp3.id, "Build a RAG pipeline with ChromaDB + OpenAI")
        add_checkpoint(cp3.id, "Deploy an AI agent to production")
        add_project(cp3.id, "AI Study Buddy",
                    "A RAG-powered chatbot that answers questions from uploaded PDFs (LangChain + FastAPI + HTMX). Deploy on Railway.")
        add_resource(cp3.id, "LangChain Docs", "https://python.langchain.com/docs/get_started/introduction", is_free=True, rtype="article")
        add_resource(cp3.id, "DeepLearning.AI Short Courses", "https://learn.deeplearning.ai/", is_free=True, rtype="course")
        add_resource(cp3.id, "Full Stack LLM Bootcamp", "https://fullstackdeeplearning.com/llm-bootcamp/", is_free=True, rtype="course")

        cp4 = add_phase("Phase 4: Portfolio & Job Search", 4,
                         "Polish three flagship AI projects, build your brand, and land interviews.", carol_roadmap.id)
        add_checkpoint(cp4.id, "Publish 3 projects with READMEs and live demos")
        add_checkpoint(cp4.id, "Apply to 5 AI Engineer roles per week")
        add_checkpoint(cp4.id, "Solve 50 ML interview questions on various platforms")
        add_project(cp4.id, "Open-Source AI Tool",
                    "Build and open-source a small AI utility (e.g., auto-summariser, code reviewer). Get 50+ GitHub stars.")
        add_resource(cp4.id, "AI Interview Handbook", "https://www.interviewquery.com/", is_free=False, rtype="tool")
        add_resource(cp4.id, "Levels.fyi – Salary Research", "https://www.levels.fyi/", is_free=True, rtype="tool")
        session.commit()

    print("✅ Seed complete — 3 users, 3 roadmaps, all phases/checkpoints/resources added.")


if __name__ == "__main__":
    seed()
