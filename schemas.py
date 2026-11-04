from datetime import datetime
from typing import List, Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    field_validator,
)


class SkillBase(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=100)
    icon_name: Optional[str] = Field(default=None, max_length=100)
    proficiency_level: str = Field(default="Intermediate", max_length=32)


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    icon_name: Optional[str] = Field(default=None, max_length=100)
    proficiency_level: Optional[str] = Field(default=None, max_length=32)


class Skill(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10_000)
    repo_url: Optional[HttpUrl] = None
    live_url: Optional[HttpUrl] = None
    tech_stack: Optional[str] = Field(default=None, max_length=20_000)

    @field_validator("repo_url", "live_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10_000)
    repo_url: Optional[HttpUrl] = None
    live_url: Optional[HttpUrl] = None
    tech_stack: Optional[str] = Field(default=None, max_length=20_000)

    @field_validator("repo_url", "live_url", mode="before")
    @classmethod
    def empty_url_to_none(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_url: Optional[str] = None
    created_at: datetime


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


class Profile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    profile_image_url: Optional[str] = None
    cv_url: Optional[str] = None


class ContactMessageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    subject: Optional[str] = Field(default=None, max_length=200)
    message: str = Field(..., min_length=10, max_length=5_000)

    @field_validator("name", "subject", "message", mode="before")
    @classmethod
    def strip_text(cls, value):
        if isinstance(value, str):
            return value.strip()
        return value


class ContactMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    subject: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime
