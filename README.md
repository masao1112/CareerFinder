# TechPath AI – IT Career Compass

TechPath AI is a full-stack web application designed to help users discover their ideal IT career path through a smart assessment and provide a personalized, step-by-step learning roadmap.

## Tech Stack
- **Backend:** FastAPI (Python) + SQLModel + SQLite
- **Frontend:** HTMX + Bootstrap 5.3 + Jinja2 Templates
- **Design:** Academic, clean navy-blue (#0d3b66) and gold (#f5c842) theme

## Features
- **Multi-step Career Assessment:** Tailored questions based on user interests or specific career paths.
- **AI-Powered Matching:** Calculates confidence scores for multiple career paths (simulated).
- **Interactive Roadmap:** A visual vertical timeline with phases, milestones, project ideas, and resources.
- **Progress Tracking:** Interactive "Mark Done" buttons to track completion of checkpoints.
- **Responsive Design:** Optimized for both desktop and mobile devices.

---

## How to Run the Web App

### 1. Install Dependencies
Ensure you have Python 3.9+ installed. Clone or copy the project files, then run:
```bash
pip install -r requirements.txt
```

### 2. Seed the Database
To populate the application with mock users (Alice, Bob, Carol) and their roadmaps, run:
```bash
python seed.py
```
This will create `techpath.db` in your local directory.

### 3. Start the Server
Run the FastAPI application using Uvicorn:
```bash
uvicorn main:app --reload --port 8000
```

### 4. Open in Browser
Once the server is running, open your browser and navigate to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## Demo Users
You can view the pre-seeded roadmaps directly:
- **Alice (Software Engineer):** [http://127.0.0.1:8000/roadmap/1](http://127.0.0.1:8000/roadmap/1)
- **Bob (Data Scientist):** [http://127.0.0.1:8000/roadmap/2](http://127.0.0.1:8000/roadmap/2)
- **Carol (AI Engineer):** [http://127.0.0.1:8000/roadmap/3](http://127.0.0.1:8000/roadmap/3)

## Project Structure
- `main.py`: Core application logic and routing.
- `models.py`: Database schema definitions using SQLModel.
- `database.py`: Database engine and session management.
- `seed.py`: Script to populate the database with initial data.
- `templates/`: Jinja2 templates for the frontend.
- `templates/partials/`: HTMX fragments for dynamic updates.
