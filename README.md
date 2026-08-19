# V-Private Media

**Private communication. Your people. Your files.**

A multi-user private communication application built as a software-engineering portfolio project. There is intentionally no public feed, follower system, reels, or public discovery.

## v1 features

- Phone + password registration/login
- Unique case-insensitive `$username` identity
- Contact search and contact list
- Persistent private 1-to-1 messages
- Private groups and membership roles
- Realtime WebSocket delivery for online users
- Offline message persistence
- Private file records, SHA-256 integrity hash and 10 MB upload limit
- Authenticated/authorized APIs
- Per-user text/accent color (white by default)
- Black transparent responsive UI
- Desktop and mobile layouts
- SQLite local database; SQLAlchemy makes migration to PostgreSQL straightforward
- Backend smoke tests
- Dockerfiles + Docker Compose
- GitHub Actions CI

## Architecture

`React client -> JWT authenticated FastAPI -> SQLAlchemy database`

`React client <-> authenticated WebSocket <-> FastAPI connection manager`

Files are validated for size, renamed with random server-side identifiers, hashed with SHA-256, and access metadata is stored in the database.

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
set SECRET_KEY=replace-with-a-long-random-secret
uvicorn app.main:app --reload
```

On Linux/macOS use `export SECRET_KEY=...` instead of `set`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally `http://localhost:5173`). API docs are available from the backend at `/docs`.

### Docker

```bash
docker compose up --build
```

## Test

```bash
cd backend
pip install pytest httpx
pytest -q
```

## Security notes

This v1 uses password hashing, JWT authentication, server-side authorization checks, input validation, randomized stored filenames, upload size limits, and file integrity hashing. It does **not** claim production-grade end-to-end encryption. E2EE requires a mature audited protocol and robust device/key lifecycle; custom cryptography is intentionally not used.

For a real public deployment, replace SQLite with PostgreSQL, configure HTTPS/WSS behind a reverse proxy, use a strong external `SECRET_KEY`, add object storage/malware scanning for uploads, rate limiting, backups, monitoring, and a mature E2EE implementation if message confidentiality from the server is required.

## Resume summary

> Built a responsive multi-user private communication platform using React, FastAPI, SQLAlchemy and WebSockets, implementing JWT authentication, unique user identities, persistent private/group messaging, role-based group membership, controlled file sharing, integrity hashing, Docker packaging and CI testing.
