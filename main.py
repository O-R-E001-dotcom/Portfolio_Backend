import os
import json
from html import escape as html_escape
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.responses import StreamingResponse
import mimetypes
import urllib.request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel
import uvicorn
from database import engine, Base, get_db
from models import Skill, Project, Profile, ContactMessage
from schemas import (
    SkillCreate,
    SkillUpdate,
    Skill as SkillOut,
    Project as ProjectOut,
    PaginatedSkills,
    PaginatedProjects,
    Token,
    Profile as ProfileOut,
    ContactMessageCreate,
    ContactMessageOut,
)
from auth import authenticate_admin, create_access_token
from deps import get_current_admin
from cloudinary_utils import (
    upload_project_image,
    delete_project_image,
    upload_profile_image,
    delete_profile_image,
    upload_cv_file,
    delete_cv_file,
)

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

load_dotenv()

# Rate limiting with Redis (fallback to in-memory for local dev)
REDIS_URL = os.getenv("REDIS_URL")
USE_REDIS = os.getenv("RATE_LIMIT_STORAGE", "redis").lower() == "redis"

def build_limiter():
    if not (USE_REDIS and REDIS_URL):
        return Limiter(key_func=get_remote_address)
    try:
        import redis  # local import to avoid hard dependency at import time
        client = redis.Redis.from_url(REDIS_URL)
        client.ping()
        return Limiter(key_func=get_remote_address, storage_uri=REDIS_URL)
    except Exception:
        # In-memory fallback if Redis is unavailable
        return Limiter(key_func=get_remote_address)

limiter = build_limiter()

app = FastAPI(title="Portfolio Backend - Admin API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS
origins_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "https://portfolio-eta-flax-91.vercel.app",
)
origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"] ,
)

# Create tables
Base.metadata.create_all(bind=engine)

class AdminLogin(BaseModel):
    email: str
    password: str


def normalize_proficiency(value):
    if value is None:
        return "Intermediate"
    if isinstance(value, str):
        return value
    try:
        num = int(value)
        if num <= 2:
            return "Beginner"
        if num == 3:
            return "Intermediate"
        return "Advanced"
    except Exception:
        return "Intermediate"


def get_or_create_profile(db: Session) -> Profile:
    profile = db.query(Profile).first()
    if profile:
        return profile
    profile = Profile()
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@app.get("/")
@limiter.limit("60/minute")
def root(request: Request):
    return {"message": "Portfolio backend is running"}


@app.get("/health")
@limiter.limit("120/minute")
def health(request: Request, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"

    return {
        "status": "ok" if database == "ok" else "degraded",
        "database": database,
    }


@app.get("/profile", response_model=ProfileOut)
@limiter.limit("60/minute")
def get_profile(request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile:
        return ProfileOut()
    return profile


@app.put("/profile", response_model=ProfileOut)
@limiter.limit("20/minute")
def update_profile(
    request: Request,
    image: Optional[UploadFile] = File(None),
    cv: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    profile = get_or_create_profile(db)

    if image:
        if profile.profile_image_public_id:
            delete_profile_image(profile.profile_image_public_id)
        uploaded = upload_profile_image(image.file)
        profile.profile_image_url = uploaded.get("url")
        profile.profile_image_public_id = uploaded.get("public_id")

    if cv:
        if profile.cv_public_id:
            delete_cv_file(profile.cv_public_id)
        uploaded = upload_cv_file(cv.file)
        profile.cv_url = uploaded.get("url")
        profile.cv_public_id = uploaded.get("public_id")

    db.commit()
    db.refresh(profile)
    return profile


@app.get("/profile/cv/download")
@limiter.limit("60/minute")
def download_cv(request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile or not profile.cv_url:
        raise HTTPException(status_code=404, detail="CV not found")

    cv_url = profile.cv_url
    clean_url = cv_url.split("?")[0]
    filename = "Abolore_Sanni_CV.pdf"
    mime_type, _ = mimetypes.guess_type(clean_url)
    media_type = mime_type or "application/octet-stream"

    def stream():
        with urllib.request.urlopen(cv_url) as resp:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    headers = {"Content-Disposition": f'attachment; filename=\"{filename}\"'}
    return StreamingResponse(stream(), media_type=media_type, headers=headers)


@app.get("/profile/cv/view")
@limiter.limit("60/minute")
def view_cv(request: Request, db: Session = Depends(get_db)):
    profile = db.query(Profile).first()
    if not profile or not profile.cv_url:
        raise HTTPException(status_code=404, detail="CV not found")

    cv_url = profile.cv_url
    media_type = "application/pdf"

    def stream():
        with urllib.request.urlopen(cv_url) as resp:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    headers = {"Content-Disposition": "inline; filename=\"Abolore_Sanni_CV.pdf\""}
    return StreamingResponse(stream(), media_type=media_type, headers=headers)

@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
def admin_login(payload: AdminLogin, request: Request):
    if not authenticate_admin(payload.email, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=payload.email)
    return {"access_token": token, "token_type": "bearer"}

# Skills
@app.get("/skills", response_model=PaginatedSkills)
@limiter.limit("60/minute")
def list_skills(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Skill).order_by(Skill.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    for s in items:
        s.proficiency_level = normalize_proficiency(s.proficiency_level)
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@app.post("/skills", response_model=SkillOut)
@limiter.limit("30/minute")
def create_skill(
    request: Request,
    payload: SkillCreate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    data = payload.dict()
    data["proficiency_level"] = normalize_proficiency(data.get("proficiency_level"))
    skill = Skill(**data)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill

@app.put("/skills/{skill_id}", response_model=SkillOut)
@limiter.limit("30/minute")
def update_skill(
    request: Request,
    skill_id: int,
    payload: SkillUpdate,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    for k, v in payload.dict(exclude_unset=True).items():
        if k == "proficiency_level":
            v = normalize_proficiency(v)
        setattr(skill, k, v)
    db.commit()
    db.refresh(skill)
    return skill

@app.delete("/skills/{skill_id}")
@limiter.limit("20/minute")
def delete_skill(
    request: Request,
    skill_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    db.delete(skill)
    db.commit()
    return {"ok": True}

# Projects
@app.get("/projects", response_model=PaginatedProjects)
@limiter.limit("60/minute")
def list_projects(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(9, ge=1, le=100),
    db: Session = Depends(get_db),
):
    q = db.query(Project).order_by(Project.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": items, "page": page, "page_size": page_size, "total": total}

@app.get("/projects/{project_id}", response_model=ProjectOut)
@limiter.limit("60/minute")
def get_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/projects", response_model=ProjectOut)
@limiter.limit("20/minute")
def create_project(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    repo_url: Optional[str] = Form(None),
    live_url: Optional[str] = Form(None),
    tech_stack: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    image_url = None
    image_public_id = None
    if image:
        uploaded = upload_project_image(image.file)
        image_url = uploaded.get("url")
        image_public_id = uploaded.get("public_id")

    project = Project(
        title=title,
        description=description,
        repo_url=(repo_url or "").strip() or None,
        live_url=(live_url or "").strip() or None,
        tech_stack=tech_stack,
        image_url=image_url,
        image_public_id=image_public_id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@app.put("/projects/{project_id}", response_model=ProjectOut)
@limiter.limit("20/minute")
def update_project(
    request: Request,
    project_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    repo_url: Optional[str] = Form(None),
    live_url: Optional[str] = Form(None),
    tech_stack: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if title is not None:
        project.title = title
    if description is not None:
        project.description = description
    if repo_url is not None:
        project.repo_url = repo_url.strip() or None
    if live_url is not None:
        project.live_url = live_url.strip() or None
    if tech_stack is not None:
        project.tech_stack = tech_stack

    if image:
        # delete old image
        if project.image_public_id:
            delete_project_image(project.image_public_id)
        uploaded = upload_project_image(image.file)
        project.image_url = uploaded.get("url")
        project.image_public_id = uploaded.get("public_id")

    db.commit()
    db.refresh(project)
    return project

@app.delete("/projects/{project_id}")
@limiter.limit("20/minute")
def delete_project(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.image_public_id:
        delete_project_image(project.image_public_id)

    db.delete(project)
    db.commit()
    return {"ok": True}

# ===== Contact =====
def send_contact_email(payload: ContactMessageCreate) -> bool:
    """Best-effort notification email via Brevo. Returns True if sent."""
    api_key = os.getenv("BREVO_API_KEY", "").strip()
    sender_email = os.getenv("BREVO_SENDER_EMAIL", "aboloresanni001@gmail.com")
    sender_name = os.getenv("BREVO_SENDER_NAME", "Portfolio")
    admin_email = os.getenv("ADMIN_EMAIL", sender_email)

    if not api_key or api_key.startswith("your_"):
        return False

    subject = payload.subject or "New portfolio message"
    safe_name = html_escape(payload.name)
    safe_email = html_escape(payload.email)
    safe_subject = html_escape(subject)
    safe_message = html_escape(payload.message)
    html = (
        f"<h2>New message from your portfolio</h2>"
        f"<p><strong>Name:</strong> {safe_name}</p>"
        f"<p><strong>Email:</strong> {safe_email}</p>"
        f"<p><strong>Subject:</strong> {safe_subject}</p>"
        f"<p><strong>Message:</strong></p>"
        f"<p style='white-space:pre-wrap'>{safe_message}</p>"
    )
    body = json.dumps(
        {
            "sender": {"name": sender_name, "email": sender_email},
            "to": [{"email": admin_email}],
            "replyTo": {"email": payload.email, "name": payload.name},
            "subject": f"Portfolio contact: {subject}",
            "htmlContent": html,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=body,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False


@app.post("/contact", response_model=ContactMessageOut, status_code=201)
@limiter.limit("5/minute")
def create_contact_message(
    request: Request,
    payload: ContactMessageCreate,
    db: Session = Depends(get_db),
):
    message = ContactMessage(
        name=payload.name.strip(),
        email=payload.email,
        subject=(payload.subject or "").strip() or None,
        message=payload.message.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    # Email delivery is best-effort; the message is always persisted.
    send_contact_email(payload)
    return message


@app.get("/contact", response_model=List[ContactMessageOut])
@limiter.limit("60/minute")
def list_contact_messages(
    request: Request,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()


@app.put("/contact/{message_id}/read", response_model=ContactMessageOut)
@limiter.limit("60/minute")
def mark_contact_message_read(
    request: Request,
    message_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    message.is_read = True
    db.commit()
    db.refresh(message)
    return message


@app.delete("/contact/{message_id}", status_code=204)
@limiter.limit("30/minute")
def delete_contact_message(
    request: Request,
    message_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(message)
    db.commit()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
