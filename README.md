# AI-Powered Career Navigator (Python FastAPI backend)

Team ByteStorm · Quantumard National Hackathon 2027

## Project structure

```
career-navigator-backend/
├── main.py            # FastAPI backend: skill detection, scoring, recommendations, roadmap, chat
├── requirements.txt   # Python packages
├── README.md
└── static/
    ├── index.html     # Web page (design from the full app)
    └── app.js         # Calls the backend API
```

## API endpoints

| Method | Endpoint        | What it does                                              |
|--------|-----------------|-----------------------------------------------------------|
| GET    | `/api/health`   | Checks the server is running                              |
| POST   | `/api/analyze`  | Detects skills, scores 3 roles, lists gaps and roadmap    |
| POST   | `/api/chat`     | AI career assistant that answers using the latest report  |

Interactive API docs appear at `/docs` once the server is running.

## Setup (Python 3.10 or newer)

```bash
cd career-navigator-backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Then open:
- **App:** http://127.0.0.1:8000
- **API docs:** http://127.0.0.1:8000/docs

## Try the API

In the docs page, open `POST /api/analyze`, click **Try it out**, and send:

```json
{ "name": "Arun", "resume": "I know Python, SQL and Git", "skills": [] }
```

## Notes

- Skill detection, scoring and recommendations run on the server.
- Recommendations use a demo catalog. Replace `CATALOG` in `main.py` with real data later.
- The database (Firebase/MongoDB) listed in the PPT is planned as future work. Data is not stored yet.
- GitHub Pages can only host static files, so this Python version runs on your own computer. To make it public later, host it on a Python-friendly service such as Render.
