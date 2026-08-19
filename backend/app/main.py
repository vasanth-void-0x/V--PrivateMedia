from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="V-Private Media API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active: dict[str, WebSocket] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active[username.lower()] = websocket

    def disconnect(self, username: str):
        self.active.pop(username.lower(), None)

    async def send_private(self, recipient: str, payload: dict) -> bool:
        socket = self.active.get(recipient.lower())
        if not socket:
            return False
        await socket.send_json(payload)
        return True


manager = ConnectionManager()


@app.get("/")
def root():
    return {"app": "V-Private Media", "status": "online", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy", "connected_users": len(manager.active)}


@app.websocket("/ws/{username}")
async def private_socket(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            recipient = data.get("to", "")
            message = data.get("message", "").strip()
            if recipient and message:
                delivered = await manager.send_private(
                    recipient,
                    {"from": f"${username}", "message": message},
                )
                await websocket.send_json(
                    {"type": "status", "to": f"${recipient}", "delivered": delivered}
                )
    except WebSocketDisconnect:
        manager.disconnect(username)
