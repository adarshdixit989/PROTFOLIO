from datetime import datetime
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, ConfigDict
from sqlalchemy import create_engine, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase): pass
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

Base.metadata.create_all(engine)

app = FastAPI(title="Adarsh Dixit Portfolio API", version="1.0.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

class MessageIn(BaseModel):
    name: str
    email: EmailStr
    subject: str
    message: str

class MessageOut(MessageIn):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

@app.get("/api/health")
def health(): return {"status":"ok","service":"portfolio-api"}

@app.get("/api/profile")
def profile():
    return {"name":"Adarsh Dixit","location":"Greater Noida, India","email":"adarshdixit998@gmail.com","phone":"+91 9569522432","linkedin":"https://www.linkedin.com/in/adarsh-dixit9","github":"https://github.com/adarshdixit989"}

@app.post("/api/messages", response_model=MessageOut, status_code=201)
def create_message(payload: MessageIn, session: Session = Depends(db)):
    if not payload.name.strip() or not payload.message.strip(): raise HTTPException(400,"Name and message are required")
    item=Message(**payload.model_dump()); session.add(item); session.commit(); session.refresh(item); return item

@app.get("/api/messages", response_model=list[MessageOut])
def messages(session: Session = Depends(db)):
    return session.query(Message).order_by(Message.created_at.desc()).all()
