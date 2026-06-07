# Resume ETL Pipeline

A production-grade, self-hosted data pipeline that dynamically compiles professional resumes.

## Features
- Treats raw career history as a structured JSON database (`master_resume.json`).
- Uses FastAPI & Pydantic v2 for data validation.
- Employs Google Gemini for AI-driven tailoring of resume points to match target job descriptions.
- Compiles resumes into professional PDFs using a Jinja2 template and LaTeX engine inside a Docker container.
