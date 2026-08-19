import hashlib
import os
import re
import uuid
from pathlib import Path
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Contact, Group, GroupMember, Message, SharedFile, User
from .security import create_token, decode_token, hash_password, verify_password

Base.metadata.create_all(bind=engine)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024
USERNAME = re.compile(r"^[a-zA-Z0-9_]{3,20}$")

app = FastAPI(title="V-Private Media API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class RegisterIn(BaseModel):
    name: str
    username: str
    phone: str
    password: str
class LoginIn(BaseModel):
    phone: str
    password: str
class ContactIn(BaseModel):
    username: str
class GroupIn(BaseModel):
    name: str
    members: list[str] = []
class MessageIn(BaseModel):
    body: str
class ColorIn(BaseModel):
    color: str


def current_user(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authentication required")
    uid = decode_token(authorization[7:])
    user = db.get(User, uid) if uid else None
    if not user:
        raise HTTPException(401, "Invalid token")
    return user

def public_user(u: User):
    return {"id": u.id, "name": u.name, "username": f"${u.username}", "accent_color": u.accent_color}

class Connections:
    def __init__(self): self.active: dict[int, WebSocket] = {}
    async def connect(self, uid: int, ws: WebSocket):
        await ws.accept(); self.active[uid] = ws
    def disconnect(self, uid: int): self.active.pop(uid, None)
    async def emit(self, uid: int, data: dict):
        ws = self.active.get(uid)
        if ws: await ws.send_json(data); return True
        return False
manager = Connections()

@app.get("/")
def root(): return {"app":"V-Private Media","status":"online","version":"1.0.0"}
@app.get("/health")
def health(): return {"status":"healthy","connected_users":len(manager.active)}

@app.post("/auth/register")
def register(data: RegisterIn, db: Session = Depends(get_db)):
    username = data.username.lower().lstrip("$").strip()
    if not USERNAME.fullmatch(username): raise HTTPException(400,"Username must be 3-20 letters, numbers or underscores")
    if len(data.password) < 8: raise HTTPException(400,"Password must be at least 8 characters")
    if db.query(User).filter(or_(User.username==username, User.phone==data.phone.strip())).first(): raise HTTPException(409,"Username or phone already registered")
    user=User(name=data.name.strip(),username=username,phone=data.phone.strip(),password_hash=hash_password(data.password)); db.add(user); db.commit(); db.refresh(user)
    return {"token":create_token(user.id),"user":public_user(user)}

@app.post("/auth/login")
def login(data: LoginIn, db: Session = Depends(get_db)):
    user=db.query(User).filter(User.phone==data.phone.strip()).first()
    if not user or not verify_password(data.password,user.password_hash): raise HTTPException(401,"Invalid credentials")
    return {"token":create_token(user.id),"user":public_user(user)}

@app.get("/me")
def me(user: User=Depends(current_user)): return public_user(user)

@app.patch("/me/color")
def color(data: ColorIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    if not re.fullmatch(r"#[0-9a-fA-F]{6}",data.color): raise HTTPException(400,"Invalid hex color")
    user.accent_color=data.color; db.commit(); return public_user(user)

@app.get("/users/search")
def search(q: str, user: User=Depends(current_user), db: Session=Depends(get_db)):
    q=q.lower().lstrip("$")
    return [public_user(x) for x in db.query(User).filter(User.username.contains(q),User.id!=user.id).limit(20).all()]

@app.post("/contacts")
def add_contact(data: ContactIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    target=db.query(User).filter(User.username==data.username.lower().lstrip("$")).first()
    if not target or target.id==user.id: raise HTTPException(404,"User not found")
    if not db.query(Contact).filter_by(owner_id=user.id,contact_id=target.id).first(): db.add(Contact(owner_id=user.id,contact_id=target.id)); db.commit()
    return public_user(target)

@app.get("/contacts")
def contacts(user: User=Depends(current_user), db: Session=Depends(get_db)):
    ids=[x.contact_id for x in db.query(Contact).filter_by(owner_id=user.id).all()]
    return [public_user(x) for x in db.query(User).filter(User.id.in_(ids)).all()] if ids else []

@app.post("/groups")
def create_group(data: GroupIn, user: User=Depends(current_user), db: Session=Depends(get_db)):
    if not data.name.strip(): raise HTTPException(400,"Group name required")
    group=Group(name=data.name.strip(),owner_id=user.id); db.add(group); db.flush(); db.add(GroupMember(group_id=group.id,user_id=user.id,role="owner"))
    for name in set(data.members):
        member=db.query(User).filter(User.username==name.lower().lstrip("$")).first()
        if member and member.id!=user.id: db.add(GroupMember(group_id=group.id,user_id=member.id,role="member"))
    db.commit(); return {"id":group.id,"name":group.name,"role":"owner"}

@app.get("/groups")
def groups(user: User=Depends(current_user), db: Session=Depends(get_db)):
    memberships=db.query(GroupMember).filter_by(user_id=user.id).all(); result=[]
    for m in memberships:
        g=db.get(Group,m.group_id); result.append({"id":g.id,"name":g.name,"role":m.role})
    return result

def ensure_group(db, gid, uid):
    if not db.query(GroupMember).filter_by(group_id=gid,user_id=uid).first(): raise HTTPException(403,"Not a group member")

@app.post("/messages/private/{recipient_id}")
async def private_message(recipient_id:int,data:MessageIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    if not db.get(User,recipient_id): raise HTTPException(404,"Recipient not found")
    body=data.body.strip()
    if not body or len(body)>4000: raise HTTPException(400,"Invalid message")
    msg=Message(sender_id=user.id,recipient_id=recipient_id,body=body); db.add(msg); db.commit(); db.refresh(msg)
    delivered=await manager.emit(recipient_id,{"type":"message","id":msg.id,"from":public_user(user),"body":body,"created_at":msg.created_at.isoformat()})
    msg.delivered=delivered; db.commit(); return {"id":msg.id,"delivered":delivered}

@app.get("/messages/private/{other_id}")
def private_history(other_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.query(Message).filter(or_((Message.sender_id==user.id)&(Message.recipient_id==other_id),(Message.sender_id==other_id)&(Message.recipient_id==user.id))).order_by(Message.created_at).limit(500).all()
    return [{"id":m.id,"sender_id":m.sender_id,"body":m.body,"delivered":m.delivered,"read":m.read,"created_at":m.created_at.isoformat()} for m in rows]

@app.post("/messages/group/{group_id}")
async def group_message(group_id:int,data:MessageIn,user:User=Depends(current_user),db:Session=Depends(get_db)):
    ensure_group(db,group_id,user.id); body=data.body.strip()
    if not body or len(body)>4000: raise HTTPException(400,"Invalid message")
    msg=Message(sender_id=user.id,group_id=group_id,body=body); db.add(msg); db.commit(); db.refresh(msg)
    members=db.query(GroupMember).filter(GroupMember.group_id==group_id,GroupMember.user_id!=user.id).all()
    for member in members: await manager.emit(member.user_id,{"type":"group_message","group_id":group_id,"from":public_user(user),"body":body})
    return {"id":msg.id}

@app.get("/messages/group/{group_id}")
def group_history(group_id:int,user:User=Depends(current_user),db:Session=Depends(get_db)):
    ensure_group(db,group_id,user.id); rows=db.query(Message).filter_by(group_id=group_id).order_by(Message.created_at).limit(500).all()
    return [{"id":m.id,"sender_id":m.sender_id,"body":m.body,"created_at":m.created_at.isoformat()} for m in rows]

@app.post("/files")
async def upload_file(recipient_id:int|None=Form(None),group_id:int|None=Form(None),file:UploadFile=File(...),user:User=Depends(current_user),db:Session=Depends(get_db)):
    if bool(recipient_id)==bool(group_id): raise HTTPException(400,"Choose exactly one recipient or group")
    if group_id: ensure_group(db,group_id,user.id)
    if recipient_id and not db.get(User,recipient_id): raise HTTPException(404,"Recipient not found")
    data=await file.read(MAX_FILE_SIZE+1)
    if len(data)>MAX_FILE_SIZE: raise HTTPException(413,"File exceeds 10 MB limit")
    ext=Path(file.filename or "file").suffix[:12]; stored=f"{uuid.uuid4().hex}{ext}"; (UPLOAD_DIR/stored).write_bytes(data)
    record=SharedFile(owner_id=user.id,recipient_id=recipient_id,group_id=group_id,original_name=Path(file.filename or "file").name,stored_name=stored,size=len(data),sha256=hashlib.sha256(data).hexdigest()); db.add(record); db.commit(); db.refresh(record)
    return {"id":record.id,"name":record.original_name,"size":record.size,"sha256":record.sha256}

@app.get("/files")
def files(user:User=Depends(current_user),db:Session=Depends(get_db)):
    group_ids=[x.group_id for x in db.query(GroupMember).filter_by(user_id=user.id).all()]
    rows=db.query(SharedFile).filter(or_(SharedFile.owner_id==user.id,SharedFile.recipient_id==user.id,SharedFile.group_id.in_(group_ids) if group_ids else False)).order_by(SharedFile.created_at.desc()).all()
    return [{"id":f.id,"name":f.original_name,"size":f.size,"sha256":f.sha256,"created_at":f.created_at.isoformat()} for f in rows]

@app.websocket("/ws")
async def socket(ws:WebSocket,token:str):
    uid=decode_token(token)
    if not uid: await ws.close(code=1008); return
    await manager.connect(uid,ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: manager.disconnect(uid)
