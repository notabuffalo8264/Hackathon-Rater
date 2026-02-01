# Hackathon-Rater

## Quick Start (Windows)

### Backend (FastAPI)

From the repo root:

1. Go to the backend folder:
   - `cd backend`
2. Create a fresh virtual environment:
   - `py -3.11 -m venv .venv`
3. Activate it:
   - `.venv\Scripts\Activate.ps1`
   - If blocked, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`
4. Install dependencies:
   - `python -m pip install --upgrade pip`
   - `pip install -r requirements.txt`
5. (Optional) Rebuild indexes after updating data files:
   - `python scripts/build_index.py`
6. Start the API server:
   - `python -m uvicorn app.main:app --reload --port 8000`

The backend will run at `http://localhost:8000`.

### Frontend (Vite + React)

From the repo root:

1. Go to the frontend folder:
   - `cd frontend`
2. Install dependencies:
   - `npm install`
3. Start the dev server:
   - `npm run dev`

Open the URL that Vite prints in the terminal.

## Data Files

Place datasets in:

- `backend/data/projects.jsonl`
- `backend/data/devpost.jsonl`

The indexer will merge both. If you change either file, rebuild the indexes:

- `python scripts/build_index.py`