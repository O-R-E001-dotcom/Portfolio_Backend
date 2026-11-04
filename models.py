from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func
from database import Base

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    icon_name = Column(String(100), nullable=True)
    proficiency_level = Column(String(32), default="Intermediate")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    repo_url = Column(String(500), nullable=True)
    live_url = Column(String(500), nullable=True)
    tech_stack = Column(Text, nullable=True)  # JSON object string
    image_url = Column(String(1000), nullable=True)
    image_public_id = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Profile(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, index=True)
    profile_image_url = Column(String(1000), nullable=True)
    profile_image_public_id = Column(String(255), nullable=True)
    cv_url = Column(String(1000), nullable=True)
    cv_public_id = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContactMessage(Base):
    __tablename__ = "contact_messages"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
