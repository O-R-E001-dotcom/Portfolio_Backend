import os
import pymysql
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

JAWSDB_URL = os.getenv("JAWSDB_URL")

# Parse the JawsDB URL: mysql+pymysql://user:pass@host:port/dbname
url = JAWSDB_URL.replace("mysql://", "").replace("mysql+pymysql://", "")
user_pass, host_db = url.split("@")
user, password = user_pass.split(":")
host_port, db = host_db.split("/")
host, port = host_port.split(":") if ":" in host_port else (host_port, 3306)

conn = pymysql.connect(
    host=host,
    user=user,
    password=password,
    database=db,
    port=int(port),
    ssl={"ssl": True}
)
cursor = conn.cursor()

# ── SKILLS ──────────────────────────────────────────
skills = [
    (4, "Frontend", "React", "FaReact", "Advanced", "2026-02-03 20:04:48"),
    (5, "Frontend", "Tailwind CSS", "", "Advanced", "2026-02-03 20:08:11"),
    (6, "Frontend", "Javascript", "", "Intermediate", "2026-02-03 20:09:19"),
    (7, "Frontend", "Redux / Context API", "react", "Intermediate", "2026-02-03 20:12:45"),
    (8, "AI", "LangGraph", "langchain", "Intermediate", "2026-02-03 20:14:34"),
    (9, "AI", "RAG", "database", "Intermediate", "2026-02-03 20:14:55"),
    (10, "AI", "Multi-Agent Systems", "ai", "Intermediate", "2026-02-03 20:15:33"),
    (11, "Backend", "FastAPI", "", "Intermediate", "2026-02-03 20:17:21"),
    (12, "Backend", "MySQL", "", "Intermediate", "2026-02-03 20:18:58"),
    (13, "Backend", "Python", "Python", "Intermediate", "2026-02-03 20:19:35"),
    (14, "AI", "Natural Language Processing", "", "Intermediate", "2026-02-03 20:20:08"),
    (15, "Tools", "Git", "", "Intermediate", "2026-02-03 20:20:27"),
    (16, "Tools", "Swagger", "", "Intermediate", "2026-02-03 20:20:38"),
    (17, "Tools", "Vercel", "", "Intermediate", "2026-02-03 20:20:50"),
    (18, "Tools", "VS Code", "", "Advanced", "2026-02-03 20:21:12"),
    (19, "AI", "Prompt Engineering", "", "Intermediate", "2026-02-03 20:22:30"),
    (20, "Tools", "Supabase", "", "Intermediate", "2026-02-03 20:22:58"),
]

print("Inserting skills...")
for skill in skills:
    cursor.execute("""
        INSERT INTO skills (id, category, name, icon_name, proficiency_level, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """, skill)

# ── PROJECTS ────────────────────────────────────────
projects = [
    (2, "SoulSync AI (Hybrid AI System)", "To make SoulSync stand out in a portfolio, you need to frame it as a Hybrid AI System rather than just a chatbot.", "https://github.com/O-R-E001-dotcom/psych-wellness", None, '{"Frontend":["React.js","Tailwind CSS"],"Backend":["FastAPI (Python)","Uvicorn"],"AI/ML":["PyTorch","Hugging Face Transformers","Gemini API","LangChain"],"Database/Auth":["Supabase","PostgreSQL"],"Infrastructure":["Docker","Docker Compose","Git"]}', "https://res.cloudinary.com/dnnrouvxh/image/upload/v1770391736/portfolio/projects/x5qv7m2ximoek1fkvraz.png", "portfolio/projects/x5qv7m2ximoek1fkvraz", "2026-02-03 20:36:41"),
    (3, "AI Study Architect: Multi-Agent PDF Intelligence", "A Full-Stack AI Learning Platform featuring Agentic Workflows and RAG-based Tutoring.", None, None, '{"Frontend":["React","Tailwind CSS","Lucide Icons","React-Markdown"],"Backend":["FastAPI (Python)","LangChain","LangGraph"],"AI/ML":["OpenAI GPT-4o","OpenAI Embeddings"],"Database & Storage":["Supabase (SQL)","ChromaDB (Vector Store)"],"PDF Processing":["PyMuPDF / LangChain Document Loaders"]}', None, None, "2026-02-03 21:10:07"),
    (4, "Shopping Assistant", "An AI that makes your shopping experience easy, and stress-free", None, None, None, None, None, "2026-02-03 22:00:18"),
    (5, "AI Tax Compliance & Advisory Assistant", "Developed an intelligent agent that leverages RAG to provide real-time tax advice and automated filing assistance.", None, None, None, None, None, "2026-02-03 22:04:50"),
]

print("Inserting projects...")
for project in projects:
    cursor.execute("""
        INSERT INTO projects (id, title, description, repo_url, live_url, tech_stack, image_url, image_public_id, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE title=VALUES(title)
    """, project)

conn.commit()
cursor.close()
conn.close()
print("✅ Migration complete!")