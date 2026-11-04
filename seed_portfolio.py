"""Seed the portfolio database with CV-grounded projects and skills.

Usage (from the backend folder):
    python seed_portfolio.py            # insert anything missing
    python seed_portfolio.py --update   # also refresh existing rows
    python seed_portfolio.py --update --prune  # also remove thin legacy rows
    python seed_portfolio.py --dry-run  # show what would change

The script is safe to run repeatedly: projects are matched by title
(normalised) and skills by name, so nothing is duplicated.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

from dotenv import load_dotenv

# `--env` loads backend/.env so the script targets the configured database
# (e.g. JAWSDB_URL in production). Without it, an unset JAWSDB_URL falls back
# to the local SQLite file used by `uvicorn main:app` in development.
if "--env" in sys.argv:
    load_dotenv()

from database import Base, SessionLocal, engine  # noqa: E402
from models import Project, Skill  # noqa: E402

from sqlalchemy import inspect, text  # noqa: E402


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").lower())


PROJECTS = [
    {
        "title": "Talyn — AI Learning Engagement Platform",
        "aliases": ["talyn"],
        "description": (
            "AI-powered learning engagement platform built end to end across three "
            "services: a FastAPI + PostgreSQL backend, a React + TypeScript frontend, "
            "and a Claude-powered AI coach. The backend exposes 15 API route modules "
            "with JWT access/refresh rotation, RBAC for learner/creator/admin roles, "
            "an immutable audit log, and Google ID-token sign-in. The coaching service "
            "has 17 endpoints grounded in a live LearnerContext (XP, streaks, quiz "
            "history, badges, missions, course progress) and is covered by 76 offline "
            "contract tests against a fake LLM client. Payments use Paystack with "
            "HMAC-SHA512 signed webhooks and a single idempotent settlement path. "
            "Delivered with Docker, GitHub Actions CI/CD, pytest/Vitest, and an "
            "operations runbook for backups and secret rotation."
        ),
        "repo_url": "",
        "live_url": "",
        "tech_stack": {
            "AI": ["Anthropic Claude API", "Prompt engineering", "LLM context grounding"],
            "Backend": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Alembic", "Redis", "PyJWT"],
            "Frontend": ["React", "TypeScript", "Vite", "Zustand", "Tailwind CSS", "Vitest"],
            "Infrastructure": ["Docker", "Docker Compose", "Caddy", "GitHub Actions", "AWS S3"],
            "Integrations": ["Paystack", "Google ID-token sign-in"],
        },
    },
    {
        "title": "ForexGPT — AI-Powered Forex Trading Platform",
        "aliases": ["forexgpt", "forex gpt"],
        "description": (
            "FastAPI backend built as one of four full-stack developers on an "
            "eight-person team (with four AI engineers) over a three-week agile "
            "sprint. Implemented authentication middleware plus the routes and "
            "services for five modules: signal extraction, AI mentor, code "
            "generation, backtesting, and quant finance. Integrated a fine-tuned "
            "Mistral 7B model through the Hugging Face Inference API and a Supabase "
            "(PostgreSQL + RLS) database, collaborating through Git branches and "
            "reviewed pull requests."
        ),
        "repo_url": "",
        "live_url": "",
        "tech_stack": {
            "AI": ["Mistral 7B", "Hugging Face Inference API", "LangChain", "Google Gemini"],
            "Backend": ["Python", "FastAPI", "Supabase", "PostgreSQL", "Authentication middleware"],
            "Workflow": ["Git", "Pull requests", "Agile sprint"],
        },
    },
    {
        "title": "SoulSync — Hybrid Psychotherapy Wellness Agent",
        "aliases": ["soulsync", "soul sync"],
        "description": (
            "Hybrid AI wellness system pairing local NLP emotion classification "
            "(DistilRoBERTa) with generative empathy (Gemini and OpenAI) to deliver "
            "secure, context-aware, CBT-informed interventions. Emotion "
            "classification feeds the LLM prompt context so responses stay grounded "
            "in structured therapeutic logic rather than open-ended generation. "
            "Designed a Supabase schema with Row-Level Security for full user-data "
            "isolation and restructured a monolithic script into a containerized, "
            "microservice-ready FastAPI/React/PostgreSQL architecture."
        ),
        "repo_url": "",
        "live_url": "",
        "tech_stack": {
            "AI": ["PyTorch", "Hugging Face Transformers", "DistilRoBERTa", "Gemini API", "LangChain"],
            "Frontend": ["React", "Tailwind CSS"],
            "Backend": ["Python", "FastAPI", "Supabase", "PostgreSQL"],
            "Infrastructure": ["Docker", "Docker Compose"],
        },
    },
    {
        "title": "My-TaxPal — AI Tax Compliance & Advisory Assistant",
        "aliases": ["mytaxpal", "my taxpal", "taxpal", "tax compliance"],
        "description": (
            "RAG-powered chatbot that demystifies Nigeria's 2025 Tax Reform Bills. "
            "Indexes official legislative documents in ChromaDB and wires LangChain "
            "retrievers so every answer is grounded in verifiable source excerpts, "
            "eliminating hallucinations on high-stakes compliance questions. A "
            "LangGraph conversation flow preserves context across multi-turn "
            "advisory sessions and explains complex scenarios in plain English."
        ),
        "repo_url": "",
        "live_url": "",
        "tech_stack": {
            "AI": ["RAG", "LangChain", "LangGraph", "ChromaDB", "Vector search"],
            "Backend": ["Python", "FastAPI"],
            "Frontend": ["React"],
        },
    },
    {
        "title": "AI Study Architect — Multi-Agent PDF Intelligence",
        "aliases": ["ai study architect", "study architect"],
        "description": (
            "Full-stack AI learning platform that turns static PDFs into an "
            "interactive study workspace. A LangGraph workflow coordinates "
            "Librarian, Scholar, Note-Taker, Examiner, and Tutor agents, with a "
            "Critic step that verifies summaries and notes before they reach the "
            "learner. A persistent ChromaDB vector store grounds the chat tutor in "
            "the uploaded document, while the Examiner generates structured "
            "multiple-choice quizzes with explanations. FastAPI streams agent "
            "progress to the React client over Server-Sent Events, and "
            "Supabase/PostgreSQL persists sessions and chat history across devices."
        ),
        "repo_url": "",
        "live_url": "",
        "tech_stack": {
            "AI": ["LangGraph", "LangChain", "OpenAI GPT-4o", "OpenAI Embeddings", "ChromaDB", "RAG"],
            "Backend": ["Python", "FastAPI", "Server-Sent Events"],
            "Frontend": ["React", "Tailwind CSS", "React Markdown"],
            "Data": ["Supabase", "PostgreSQL"],
            "Processing": ["PyMuPDF", "LangChain document loaders"],
        },
    },
    {
        "title": "Olayinka & Adebobola — Wedding Website",
        "aliases": ["wedding"],
        "description": (
            "An elegant, fully responsive wedding website for a December 2026 "
            "celebration at the Grand Ballroom, Ibadan. Opens with a cinematic video "
            "montage and falling-petal animation, then reveals a countdown timer, "
            "story timeline, event details, gallery, and a music player. Guests "
            "unlock personalized RSVP access with invite codes, and responses are "
            "written to a Google Sheet through a Google Apps Script web app. Built "
            "with React 19 and Vite with a strong focus on motion, typography, and "
            "mobile-first layout."
        ),
        "repo_url": "https://github.com/O-R-E001-dotcom/Wedding-project",
        "live_url": "",
        "tech_stack": {
            "Frontend": ["React 19", "Vite", "CSS animations", "Responsive design"],
            "Features": ["Video montage", "Countdown timer", "Story timeline", "Gallery", "Music player"],
            "Integrations": ["Google Apps Script", "Google Sheets RSVP", "Guest invite codes"],
        },
    },
]


# Legacy rows from earlier portfolio versions that are too thin or duplicate
# better case studies. Only removed when `--prune` is passed explicitly.
LEGACY_PROJECTS = ["Shopping Assistant"]


SKILLS = [
    # AI & Agent Engineering
    ("AI & Agent Engineering", "LangGraph", "ai", "Advanced"),
    ("AI & Agent Engineering", "LangChain", "ai", "Advanced"),
    ("AI & Agent Engineering", "RAG Pipelines", "llm", "Advanced"),
    ("AI & Agent Engineering", "Azure AI Foundry", "azure", "Intermediate"),
    ("AI & Agent Engineering", "Copilot Studio", "ai", "Intermediate"),
    ("AI & Agent Engineering", "Anthropic Claude API", "llm", "Advanced"),
    ("AI & Agent Engineering", "OpenAI GPT-4", "llm", "Advanced"),
    ("AI & Agent Engineering", "Gemini API", "ai", "Advanced"),
    ("AI & Agent Engineering", "Hugging Face Transformers", "ai", "Advanced"),
    ("AI & Agent Engineering", "MCP & A2A", "network", "Intermediate"),
    ("AI & Agent Engineering", "Prompt Engineering", "ai", "Advanced"),
    # RAG & Knowledge Systems
    ("RAG & Knowledge Systems", "ChromaDB", "database", "Advanced"),
    ("RAG & Knowledge Systems", "Azure AI Search", "azure", "Intermediate"),
    ("RAG & Knowledge Systems", "Vector Search", "database", "Advanced"),
    ("RAG & Knowledge Systems", "Content Grounding", "llm", "Advanced"),
    # Languages
    ("Languages", "Python", "python", "Advanced"),
    ("Languages", "JavaScript", "javascript", "Advanced"),
    ("Languages", "TypeScript", "typescript", "Advanced"),
    ("Languages", "SQL", "database", "Advanced"),
    # Backend & APIs
    ("Backend & APIs", "FastAPI", "fastapi", "Advanced"),
    ("Backend & APIs", "REST API Design", "server", "Advanced"),
    ("Backend & APIs", "SQLAlchemy", "database", "Advanced"),
    ("Backend & APIs", "Alembic", "database", "Intermediate"),
    ("Backend & APIs", "Pydantic", "python", "Advanced"),
    ("Backend & APIs", "JWT & RBAC", "server", "Advanced"),
    ("Backend & APIs", "pytest", "python", "Advanced"),
    # Frontend
    ("Frontend", "React", "react", "Advanced"),
    ("Frontend", "React Router", "react", "Advanced"),
    ("Frontend", "Zustand", "react", "Intermediate"),
    ("Frontend", "Tailwind CSS", "css", "Advanced"),
    ("Frontend", "Vite", "javascript", "Advanced"),
    ("Frontend", "Vitest", "javascript", "Intermediate"),
    # Machine Learning
    ("Machine Learning", "PyTorch", "ai", "Intermediate"),
    ("Machine Learning", "scikit-learn", "python", "Intermediate"),
    ("Machine Learning", "DistilRoBERTa", "ai", "Advanced"),
    ("Machine Learning", "Emotion Classification", "ai", "Advanced"),
    # Databases, Cloud & DevOps
    ("Databases & Cloud", "PostgreSQL", "postgres", "Advanced"),
    ("Databases & Cloud", "Redis", "database", "Intermediate"),
    ("Databases & Cloud", "Supabase", "database", "Advanced"),
    ("Databases & Cloud", "Microsoft Azure", "azure", "Intermediate"),
    ("Databases & Cloud", "AWS S3", "aws", "Intermediate"),
    ("DevOps", "Docker", "docker", "Advanced"),
    ("DevOps", "Docker Compose", "docker", "Advanced"),
    ("DevOps", "GitHub Actions", "git", "Advanced"),
    ("DevOps", "CI/CD", "git", "Advanced"),
]


def _find_project(db, aliases: list[str]):
    keys = [_normalise(alias) for alias in aliases if alias]
    for project in db.query(Project).all():
        existing = _normalise(project.title)
        if any(key and (key == existing or key in existing) for key in keys):
            return project
    return None


def _skill_index(db) -> dict[str, Skill]:
    return {_normalise(skill.name): skill for skill in db.query(Skill).all()}


def _find_exact_project(db, title: str):
    key = _normalise(title)
    for project in db.query(Project).all():
        if _normalise(project.title) == key:
            return project
    return None


def ensure_schema() -> None:
    """Create tables and widen `projects.tech_stack` on existing databases.

    The seeded tech stacks are JSON objects and routinely exceed the original
    VARCHAR(500). `create_all` never alters existing tables, so production
    MySQL/PostgreSQL needs an explicit ALTER.
    """
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if not inspector.has_table("projects"):
        return

    columns = {column["name"]: column for column in inspector.get_columns("projects")}
    tech_stack = columns.get("tech_stack")
    if tech_stack is None:
        return

    dialect = engine.dialect.name
    length = getattr(tech_stack["type"], "length", None)

    try:
        if dialect in {"mysql", "mariadb"} and length is not None and length < 2000:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE projects MODIFY COLUMN tech_stack TEXT NULL")
                )
            print("[schema] widened projects.tech_stack to TEXT")
        elif dialect == "postgresql" and tech_stack["type"].__class__.__name__.lower() != "text":
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE projects ALTER COLUMN tech_stack TYPE TEXT")
                )
            print("[schema] widened projects.tech_stack to TEXT")
    except Exception as exc:  # noqa: BLE001
        print(f"[schema] could not alter tech_stack ({exc}); continuing")


def _project_payload(item: dict) -> dict:
    return {
        "title": item["title"],
        "description": item["description"],
        "repo_url": item["repo_url"] or None,
        "live_url": item["live_url"] or None,
        "tech_stack": json.dumps(item["tech_stack"]),
    }


def seed(update: bool = False, dry_run: bool = False, prune: bool = False) -> int:
    target = engine.url
    safe_target = target.render_as_string(hide_password=True) if hasattr(target, "render_as_string") else str(target)
    print(f"Target database: {safe_target}\n")

    ensure_schema()
    db = SessionLocal()
    changes = 0

    try:
        for item in PROJECTS:
            existing = _find_project(db, item["aliases"] + [item["title"]])
            payload = _project_payload(item)

            if existing is None:
                print(f"[project] + {item['title']}")
                changes += 1
                if not dry_run:
                    db.add(Project(**payload))
            elif update:
                print(f"[project] ~ {existing.title}")
                changes += 1
                if not dry_run:
                    for field, value in payload.items():
                        setattr(existing, field, value)
            else:
                print(f"[project] = {existing.title} (exists)")

        if prune:
            for title in LEGACY_PROJECTS:
                existing = _find_exact_project(db, title)
                if existing is None:
                    continue
                print(f"[project] - {existing.title}")
                changes += 1
                if not dry_run:
                    db.delete(existing)

        skill_index = _skill_index(db)
        for category, name, icon_name, level in SKILLS:
            existing = skill_index.get(_normalise(name))
            if existing is None:
                print(f"[skill]   + {category} / {name}")
                changes += 1
                if not dry_run:
                    skill = Skill(
                        category=category,
                        name=name,
                        icon_name=icon_name,
                        proficiency_level=level,
                    )
                    db.add(skill)
                    skill_index[_normalise(name)] = skill
            elif update and (
                existing.category != category
                or existing.icon_name != icon_name
                or existing.proficiency_level != level
            ):
                print(f"[skill]   ~ {existing.name} -> {category}")
                changes += 1
                if not dry_run:
                    existing.category = category
                    existing.icon_name = icon_name
                    existing.proficiency_level = level
            else:
                print(f"[skill]   = {existing.name} (exists)")

        if not dry_run:
            db.commit()

        print(f"\n{'Would apply' if dry_run else 'Applied'} {changes} change(s).")
        return changes
    finally:
        db.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed portfolio projects and skills.")
    parser.add_argument("--update", action="store_true", help="Refresh existing rows too.")
    parser.add_argument(
        "--prune",
        action="store_true",
        help="Delete thin legacy projects listed in LEGACY_PROJECTS.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing.")
    parser.add_argument(
        "--env",
        action="store_true",
        help="Load backend/.env first (targets JAWSDB_URL if set).",
    )
    args = parser.parse_args()
    seed(update=args.update, dry_run=args.dry_run, prune=args.prune)
    return 0


if __name__ == "__main__":
    sys.exit(main())
