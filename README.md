# V-Private Media

**Private communication. Your people. Your files.**

V-Private Media is a privacy-focused multi-user communication platform for private 1-to-1 chats, private groups, contacts, and file sharing. It intentionally has no public feed, followers, reels, or social-media discovery.

## Product direction

- `$username` identity system
- Private 1-to-1 conversations
- Private groups with owner/admin/member roles
- Contact management
- Realtime messaging with WebSockets
- Private file sharing with validation and access control
- Sent, delivered, and read states
- Online/offline presence
- Responsive desktop and mobile UI
- Black transparent interface with white as the default text color
- Optional per-user text/accent color preference

## Planned stack

- Frontend: React + Vite
- Backend: FastAPI + Python
- Database: PostgreSQL (SQLite supported for local development)
- Realtime: WebSockets
- Authentication: JWT + password hashing
- Testing: Pytest
- Deployment: Docker

## Security direction

V-Private Media will use authenticated APIs, authorization checks, input/file validation, rate limiting, and established cryptographic libraries. Custom cryptographic algorithms will not be invented for the project.

> Current status: active development — foundation phase.
