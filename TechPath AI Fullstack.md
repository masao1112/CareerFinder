# TechPath AI - Fullstack WebApp Development Specification
**For Coding Agent**  
**Project Version:** 1.0 (March 2026)  
**Backend:** FastAPI (Python) + SQLModel + SQLite  
**Frontend:** HTMX + Bootstrap 5 + Jinja2 (NO React, NO Tailwind)  
**Theme:** Academic / Professional – clean white background, navy-blue accents (#0d3b66), soft gray text, sans-serif fonts (system-ui), subtle shadows, card-based layout. Keep it lightweight, fast-loading, and university-lab style.

---

## 1. Project Overview (from TechPathAI-Overview.docx)
- **Goal:** Multi-step IT career quiz → AI scoring → RAG-powered personalized roadmap → Interactive timeline.
- **Core Deliverable:** One JSON-driven "Systematic Roadmap" per user (phases, checkpoints, projects, free/paid resources).
- **User Journey:** Assessment → Analysis → Research → Visualization (exactly as described in section 3 of the overview doc).

---

## 2. Database – Exact ERD Implementation
Implement **exactly** the schema shown in the attached ERD image (`TechPath AI - Entity Relationship Diagram`).

Use **SQLModel** models:

```python
# models.py (copy-paste ready)
class User(SQLModel, table=True): ...
class Assessment(SQLModel, table=True): ...
class MatchResult(SQLModel, table=True): ...
class Roadmap(SQLModel, table=True): ...
class Phase(SQLModel, table=True): ...
class Checkpoint(SQLModel, table=True): ...
class ProjectIdea(SQLModel, table=True): ...
class Resource(SQLModel, table=True): ...
Copy every field name, type, FK, and comment from the ERD (including session_id, raw survey JSON, top_matches: json, overall_progress, etc.).
Use SQLite file techpath.db. Add indexes on session_id and user_id.
```
## 3. Frontend Choice & Style

Stack: FastAPI + Jinja2 templates + HTMX + Bootstrap 5.3 (via CDN for speed).
Why? Fully dynamic (multi-step quiz without page reloads), zero heavy JS frameworks, academic-friendly.
Pages / Routes:
/ → Hero + "Start Your Roadmap" button
/assessment → Multi-step wizard (HTMX swaps)
/roadmap/{roadmap_id} → Main visualization page

Academic Theme:
Navbar: dark navy with "TechPath AI" logo + university-style "Career Compass" tagline
Cards with light borders, blue headers
Progress bars in teal
Icons: Heroicons (inline SVG) or Bootstrap icons

## 4. Quiz Implementation (from questions.txt)
Exact flow:

Part 1 (always first) – Radio buttons (11 options). Store selected_path.
Part 2 (always) – General Profile + Time Availability (selects + multi-select + text).
Conditional:
If selected_path = "Not yet known" → show Part 3 (Undecided Discovery – 1-5 scales + open fields)
Else → show Part 4 (Job-Specific Skills – dynamic list based on chosen job + 3 common open questions)

Submit → POST to /api/submit-assessment → save full JSON in Assessment table.

Use HTMX for step navigation (no full reloads).
All questions must match the document word-for-word (copy the text, scales, examples).

## 5. CRITICAL INSTRUCTION: Mock Data First (for Visualization)
Before writing any AI/RAG code, please:
Seed the database with 3 complete mock users (different paths: Software Engineer, Data Scientist, Undecided → AI Engineer).
Pre-populate:
Assessment with realistic JSON payloads
MatchResult with top_matches percentages
Roadmap + 3–4 Phases + Checkpoints + ProjectIdeas + Resources

Example mock roadmap title: "Your 9-Month Web Developer Roadmap"
This allows immediate testing of the /roadmap/{id} page without needing OpenAI/Anthropic or RAG yet.

## 6. Roadmap Visualization Page (Main Deliverable)
Must look and feel like the attached "roadmap.sh-style image" (the bright yellow boxes, vertical flow, side branches for tools, checkmarks, AI chat bubble at bottom).
Requirements:
- Vertical timeline (Bootstrap list-group or custom CSS)
- Yellow/gold phase cards (exactly like the image)
- Connected lines (CSS pseudo-elements or simple SVG)
- Side branches for:
    - Resources (free/paid badges)
    - Project Ideas
    - Checkpoints (with "Mark Complete" HTMX button)

Progress ring at top (overall_progress %)
"AI Tutor – Have a question?" floating chat (placeholder for later)
Printable / Shareable button (future)

Use the exact component names from the ERD (Phase.name, Checkpoint.description, Resource.url, etc.).

7. Roadmap.sh Style Reference (text version for you to copy into the UI)
Reference the attached image (the one with "Internet → HTML → CSS → JavaScript" and side branches).
Here is the exact structure you should replicate for every career roadmap (example for Web Developer):
textInternet
   ├── How does the internet work?
   ├── What is HTTP?
   ├── DNS & Hosting
   └── Browsers

HTML → CSS → JavaScript
   ├── Version Control
   │    ├── Git
   │    ├── GitHub + GitLab
   │    └── VCS Hosting
   ├── Package Managers
   │    ├── npm / yarn / pnpm
   │    └── Bun
   ├── CSS Frameworks
   │    └── Tailwind (mock)
   └── Frontend Frameworks
        ├── React / Vue / Angular
For each career path, the phases will be:

Phase 1: Foundations
Phase 2: Core Skills
Phase 3: Tools & Frameworks
Phase 4: Projects & Portfolio
Phase 5: Job Search & Continuous Learning

Implement this exact visual language (yellow boxes, purple checkmarks, blue connections).

8. Next Steps After Mock Data
Once the mock visualization works perfectly:

Add real OpenAI/Anthropic scoring endpoint
Add ChromaDB/FAISS RAG (job data from overview doc)
User dashboard (list of saved roadmaps)

Ready to code?
Start with:
models.py + DB init + mock seed script
Basic FastAPI routes + Jinja2 base template (Bootstrap + HTMX)
Quiz wizard (Part 1 → conditional steps)
Mock roadmap page (copy the visual style from the image)

Ping me when the mock roadmap page is live – I’ll review and we’ll add the AI layer next.
Let’s build TechPath AI! 🚀
