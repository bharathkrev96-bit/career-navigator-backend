"""AI-Powered Career Navigator - FastAPI backend.

Run:   uvicorn main:app --reload
Open:  http://127.0.0.1:8000
Docs:  http://127.0.0.1:8000/docs
"""
import json
import re
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
PROFILES_FILE = DATA_DIR / "profiles.json"

app = FastAPI(title="AI-Powered Career Navigator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Words that signal each skill in a resume
ALIASES = {
    "Python": ["python"],
    "JavaScript": ["javascript", "js"],
    "HTML/CSS": ["html", "css"],
    "React": ["react", "react.js", "reactjs"],
    "Tailwind CSS": ["tailwind"],
    "FastAPI": ["fastapi"],
    "SQL": ["sql", "mysql", "postgresql"],
    "Git": ["git", "github"],
    "Docker": ["docker"],
    "REST APIs": ["rest api", "rest apis", "restful"],
    "Machine Learning": ["machine learning", "scikit-learn", "tensorflow", "pytorch"],
    "Pandas": ["pandas", "numpy"],
    "Statistics": ["statistics", "statistical"],
    "Data Visualization": ["matplotlib", "seaborn", "power bi", "tableau"],
}

# Target roles: required skills with importance weights (1 = nice to have, 3 = critical)
ROLES = {
    "Frontend Developer": {"JavaScript": 3, "HTML/CSS": 3, "React": 3, "Tailwind CSS": 2, "Git": 1},
    "Backend Developer": {"Python": 3, "FastAPI": 3, "SQL": 2, "REST APIs": 3, "Docker": 2, "Git": 1},
    "ML / Data Analyst": {"Python": 3, "Pandas": 3, "Machine Learning": 3, "Statistics": 2, "SQL": 2, "Data Visualization": 2},
}

# Demo catalog of internships, hackathons and courses
CATALOG = [
    {"kind": "Internship", "title": "Frontend Engineering Intern", "role": "Frontend Developer", "note": "Build UI components with React and Tailwind."},
    {"kind": "Internship", "title": "Backend Engineering Intern", "role": "Backend Developer", "note": "Design REST APIs and data services."},
    {"kind": "Internship", "title": "Data Analyst Intern", "role": "ML / Data Analyst", "note": "Analyze datasets and build dashboards."},
    {"kind": "Hackathon", "title": "Open Web Build Sprint", "role": "Frontend Developer", "note": "A 48-hour team challenge on web apps."},
    {"kind": "Hackathon", "title": "Applied AI Hack Day", "role": "ML / Data Analyst", "note": "Solve a real problem with ML models."},
    {"kind": "Hackathon", "title": "API Design Challenge", "role": "Backend Developer", "note": "Ship a secure, documented API in a day."},
    {"kind": "Course", "title": "React Essentials", "skill": "React", "note": "Components, state and hooks."},
    {"kind": "Course", "title": "Tailwind CSS Crash Course", "skill": "Tailwind CSS", "note": "Utility-first styling for modern UIs."},
    {"kind": "Course", "title": "FastAPI Basics", "skill": "FastAPI", "note": "Build fast Python APIs."},
    {"kind": "Course", "title": "Docker for Developers", "skill": "Docker", "note": "Containerize and deploy your projects."},
    {"kind": "Course", "title": "Git & GitHub Fundamentals", "skill": "Git", "note": "Version control for every developer."},
    {"kind": "Course", "title": "SQL for Data Work", "skill": "SQL", "note": "Query, join and aggregate data."},
    {"kind": "Course", "title": "Machine Learning Foundations", "skill": "Machine Learning", "note": "Core models, training and evaluation."},
    {"kind": "Course", "title": "Pandas & Data Cleaning", "skill": "Pandas", "note": "Prepare data for analysis."},
    {"kind": "Course", "title": "Statistics for Data Science", "skill": "Statistics", "note": "Distributions, tests and inference."},
]

WEIGHT_LABEL = {3: "critical", 2: "important", 1: "nice to have"}

# Sample mentors for mentor matching (demo profiles, replace with real mentors later)
MENTORS = {
    "Frontend Developer": [
        {"name": "Sample Mentor A", "note": "Frontend engineer · React and UI design (demo profile)"},
        {"name": "Sample Mentor B", "note": "Web developer · accessibility and performance (demo profile)"},
    ],
    "Backend Developer": [
        {"name": "Sample Mentor C", "note": "Backend engineer · Python APIs and databases (demo profile)"},
        {"name": "Sample Mentor D", "note": "Cloud engineer · deployment and DevOps (demo profile)"},
    ],
    "ML / Data Analyst": [
        {"name": "Sample Mentor E", "note": "Data scientist · machine learning and statistics (demo profile)"},
        {"name": "Sample Mentor F", "note": "Data analyst · dashboards and reporting (demo profile)"},
    ],
}

# Interview practice questions for each role
INTERVIEW = {
    "Frontend Developer": [
        "What is the difference between let, const and var?",
        "What is the CSS box model?",
        "How is React state different from props?",
        "What does responsive design mean, and how do you build it?",
    ],
    "Backend Developer": [
        "What is the difference between PUT and PATCH?",
        "What does a REST API need to be considered RESTful?",
        "What is the difference between a 404 and a 500 status code?",
        "How would you secure an API endpoint?",
    ],
    "ML / Data Analyst": [
        "What is overfitting, and how do you prevent it?",
        "What is the difference between precision and recall?",
        "What is the difference between supervised and unsupervised learning?",
        "How would you handle missing values in a dataset?",
    ],
}


class AnalyzeRequest(BaseModel):
    name: str = Field("", max_length=40)
    resume: str = Field("", max_length=10000)
    skills: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=200)
    report: dict | None = None


def detect_skills(text: str) -> set[str]:
    """Find skills mentioned as whole words in the resume text."""
    lower = text.lower()
    found = set()
    for skill, words in ALIASES.items():
        for word in words:
            if re.search(r"\b" + re.escape(word) + r"\b", lower):
                found.add(skill)
                break
    return found


def role_scores(owned: set[str]) -> dict[str, int]:
    """Percent match per role: earned weight divided by total weight."""
    scores = {}
    for role, required in ROLES.items():
        total = sum(required.values())
        earned = sum(w for skill, w in required.items() if skill in owned)
        scores[role] = round(earned / total * 100)
    return scores


def build_report(name: str, owned: set[str]) -> dict:
    scores = role_scores(owned)
    best_role = max(scores, key=scores.get)
    required = ROLES[best_role]

    gaps = sorted(
        [
            {"skill": skill, "weight": w, "level": WEIGHT_LABEL[w]}
            for skill, w in required.items()
            if skill not in owned
        ],
        key=lambda g: -g["weight"],
    )
    gap_skills = {g["skill"] for g in gaps}

    opportunities = [c for c in CATALOG if c["kind"] != "Course" and c["role"] == best_role]
    courses = [c for c in CATALOG if c["kind"] == "Course" and c.get("skill") in gap_skills]

    roadmap = [
        {
            "week": i + 1,
            "title": f"Learn {g['skill']}",
            "text": f"Finish a starter course, then build a small feature using {g['skill']}.",
        }
        for i, g in enumerate(gaps[:4])
    ]
    roadmap.append({
        "week": len(roadmap) + 1,
        "title": "Capstone project",
        "text": f"Combine your skills into one {best_role} project and publish it on GitHub.",
    })

    return {
        "name": name,
        "skills": sorted(owned),
        "scores": scores,
        "best_role": best_role,
        "best_pct": scores[best_role],
        "gaps": gaps,
        "opportunities": opportunities,
        "courses": courses,
        "roadmap": roadmap,
        "interview": INTERVIEW[best_role],
        "mentors": MENTORS[best_role],
    }


def chat_reply(question: str, report: dict | None) -> str:
    """Keyword-based career assistant that uses the latest report."""
    if not report:
        return "Run the analysis first, then ask me again."

    q = question.lower()
    role = report["best_role"]
    gaps = report["gaps"]

    if re.search(r"\b(gap|gaps|missing|learn|skill|skills|start|first)\b", q):
        if not gaps:
            return f"You already cover the core skills for {role}. Next, build a portfolio project."
        return f"Start with {gaps[0]['skill']}, since it's the most important skill for {role}."

    if re.search(r"\b(intern|internship|internships|job|jobs|hackathon|hackathons|opportunity|opportunities)\b", q):
        return f"For {role}, look at the internships and hackathons in your recommendations list."

    if re.search(r"\b(roadmap|plan|week|weeks|path)\b", q):
        return "Work through your skill gaps one at a time, then build one project that uses them together."

    if re.search(r"\b(hi|hello|hey)\b", q):
        return "Hi! Ask me about your skill gaps, internships, hackathons or your roadmap."

    return f"Your best match is {role} ({report['best_pct']}%). Ask about your gaps, opportunities or roadmap."


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI-Powered Career Navigator"}


@app.post("/api/analyze")
def analyze(req: AnalyzeRequest):
    owned = detect_skills(req.resume) | {s for s in req.skills if s in ALIASES}
    return build_report(req.name.strip(), owned)


@app.post("/api/chat")
def chat(req: ChatRequest):
    return {"answer": chat_reply(req.question, req.report)}


class SaveRequest(BaseModel):
    report: dict


def load_profiles() -> dict:
    if not PROFILES_FILE.exists():
        return {}
    return json.loads(PROFILES_FILE.read_text(encoding="utf-8"))


def write_profiles(profiles: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    PROFILES_FILE.write_text(json.dumps(profiles, indent=2), encoding="utf-8")


@app.post("/api/profiles")
def save_profile(req: SaveRequest):
    profile_id = uuid.uuid4().hex[:8]
    profiles = load_profiles()
    profiles[profile_id] = req.report
    write_profiles(profiles)
    return {"id": profile_id}


@app.get("/api/profiles/{profile_id}")
def get_profile(profile_id: str):
    profiles = load_profiles()
    if profile_id not in profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profiles[profile_id]


# Serve the web page (static/index.html and static/app.js).
# Mounted last so the /api routes above take priority.
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
