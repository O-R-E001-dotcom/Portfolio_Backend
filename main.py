import os
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pydantic import BaseModel

from database import engine, Base, get_db
from models import Skill, Project
from schemas import (
    SkillCreate,
    SkillUpdate,
    Skill as SkillOut,
    Project as ProjectOut,
    PaginatedSkills,
    PaginatedProjects,
    Token,
)
from auth import authenticate_admin, create_access_token
from deps import get_current_admin
from cloudinary_utils import upload_project_image, delete_project_image

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
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173")
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

@app.get("/")
@limiter.limit("60/minute")
def root(request: Request):
    return {"message": "Portfolio backend is running"}

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
        repo_url=repo_url,
        live_url=live_url,
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
        project.repo_url = repo_url
    if live_url is not None:
        project.live_url = live_url
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
