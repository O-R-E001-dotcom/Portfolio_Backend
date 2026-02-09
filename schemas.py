from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime

class SkillBase(BaseModel):
    category: str
    name: str
    icon_name: Optional[str] = None
    proficiency_level: str = "Intermediate"

class SkillCreate(SkillBase):
    pass

class SkillUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    icon_name: Optional[str] = None
    proficiency_level: Optional[str] = None

class Skill(SkillBase):
    id: int
    created_at: datetime
    class Config:
        orm_mode = True

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None
    repo_url: Optional[HttpUrl] = None
    live_url: Optional[HttpUrl] = None
    tech_stack: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    repo_url: Optional[HttpUrl] = None
    live_url: Optional[HttpUrl] = None
    tech_stack: Optional[str] = None

class Project(ProjectBase):
    id: int
    image_url: Optional[str] = None
    created_at: datetime
    class Config:
        orm_mode = True

class PaginatedSkills(BaseModel):
    items: List[Skill]
    page: int
    page_size: int
    total: int

class PaginatedProjects(BaseModel):
    items: List[Project]
    page: int
    page_size: int
    total: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"