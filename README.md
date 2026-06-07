# Project Antigravity: Resume ETL Pipeline

A production-grade, self-hosted data pipeline that dynamically compiles and tailors professional resumes. By treating raw career history as a structured JSON database and the presentation layer as a compiled LaTeX view, this system decouples resume content from typesetting and automates tailoring workflows using Google Gemini.

---

## Key Features

- **Strict Decoupling of Data & Presentation**: Work history and skills are maintained in a structured JSON database, completely independent of visual layout.
- **Custom Jinja2 LaTeX Renderer**: Utilizes custom tokens (`((* *))` for blocks, `((( )))` for variables) to prevent curly-brace collisions with LaTeX command structures.
- **Robust Character Escaping**: Implements recursive string escaping to safely convert special characters (e.g. `&`, `%`, `$`, `_`, `#`, `{`, `}`) to LaTeX-safe formatting, ensuring zero document build breaks.
- **Gemini Structured Tailoring**: Integrates the modern Google GenAI SDK (`google-genai`) to rewrite and align bullet points against a target Job Description (JD). Structured output is enforced by feeding the Pydantic schema to Gemini's `response_schema` to guarantee format compliance with zero hallucinations of critical credentials (dates, companies, titles).
- **Subprocess LaTeX Compiler**: Auto-detects local `pdflatex` or seamlessly falls back to executing the compilation inside a standard `texlive/texlive` Docker container.
- **RESTful Endpoints**: Exposes endpoints via FastAPI for direct compilation (bypassing AI) and tailored compilation (leveraging Gemini). Supports dynamic client-side API keys via headers.
- **Production-Grade Containerization**: Single `Dockerfile` packaging FastAPI with Python 3.11 and TeX Live (including `sourcesanspro` fonts), compiling PDFs natively.

---

## Directory Structure

```text
Resume_Updater/
├── app/
│   ├── main.py                 # FastAPI Web API Gateway & Routing
│   ├── models/
│   │   └── schema.py           # Pydantic v2 Resume Data Models
│   ├── services/
│   │   ├── compiler.py         # Subprocess compiler (local/Docker fallback)
│   │   ├── llm_transformer.py  # Gemini AI Structured Output Tailoring
│   │   └── renderer.py         # Custom Jinja2 delimiters & LaTeX escaper
│   └── data/
│       └── master_resume.json  # Candidate profile JSON database (source of truth)
├── templates/
│   └── resume_template.tex     # LaTeX layout template (TLCresume Overleaf style)
├── output/                     # Generated PDFs and rendered tex preview files
├── Dockerfile                  # Self-contained Python + TeX Live environment
├── pyproject.toml              # Dependencies config (uv standards)
└── .env                        # Local secret configurations
```

---

## API Endpoints

### 1. `GET /health`
Verifies server health and status.
- **Response**: `{"status": "healthy", "service": "resume-etl-pipeline"}`

### 2. `POST /compile/direct`
Compiles the raw JSON payload directly to a PDF without AI optimization.
- **Request Body**: `Resume` JSON object.
- **Response**: Streams back the compiled PDF file.

### 3. `POST /compile/tailor`
Tailors the work experience and project bullets to a Job Description using Gemini and returns the compiled PDF.
- **Request Body**:
  ```json
  {
    "resume": { ... },
    "job_description": "We are looking for a Python Developer..."
  }
  ```
- **Optional Header**: `X-Gemini-API-Key` to override the server-side default API key.
- **Response**: Streams back the optimized, compiled PDF file.

---

## Installation & Setup

Ensure you have **Python 3.11+** and **Docker Desktop** installed.

### 1. Local Development Setup
Clone and initialize the virtual environment using `uv`:
```powershell
# Create environment
uv venv

# Activate environment
.venv\Scripts\activate

# Install dependencies in editable mode
uv pip install -e .
```

### 2. Secrets Configuration
Create a `.env` file in the root directory and add your Google AI Studio API key:
```env
GEMINI_API_KEY=your_google_gemini_api_key
```

---

## Verification & Tests

Four test scripts are included to verify individual compilation stages:

1. **Verify Local Renderer and Docker Fallback Compiler**:
   ```powershell
   & .venv\Scripts\python.exe test_phase1.py
   ```
   *Renders `master_resume.json` to LaTeX and compiles it to `output/resume_test.pdf` using a local container.*

2. **Verify Local REST API endpoints**:
   ```powershell
   & .venv\Scripts\python.exe test_phase2.py
   ```
   *Spins up FastAPI locally, posts the payload, and saves the result to `output/resume_api_test.pdf`.*

3. **Verify Gemini AI Tailoring (Diff Display)**:
   ```powershell
   & .venv\Scripts\python.exe test_phase3.py
   ```
   *Sends the resume to Gemini, prints a console comparison of original vs. optimized bullets, and outputs `output/resume_tailored_test.pdf`.*

4. **Verify Containerized Server & Native Compilation**:
   ```powershell
   & .venv\Scripts\python.exe test_phase2_docker.py
   ```
   *Builds the production Docker image, starts the container, runs compilation natively inside it without host dependencies, and saves `output/resume_docker_api_test.pdf`.*

---

## Container Deployment

To run the full FastAPI server in production mode at port `8000`:

```powershell
# Build the production image
docker build -t resume-etl-pipeline:latest .

# Run the container
docker run -d --name resume-etl-api --env-file .env -p 8000:8000 resume-etl-pipeline:latest
```
