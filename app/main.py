import os
import uuid
import tempfile
import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from app.models.schema import Resume
from app.services.renderer import LaTeXRenderer
from app.services.compiler import LaTeXCompiler
from app.services.llm_transformer import ResumeLLMTransformer

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ResumeETLApi")

app = FastAPI(
    title="Project Antigravity: Resume ETL Pipeline API",
    description="A FastAPI backend to dynamically compile professional resumes using LaTeX and Gemini AI.",
    version="1.0.0"
)

# Initialize services
# Use templates directory in root
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
renderer = LaTeXRenderer(templates_dir=TEMPLATES_DIR)

# Use LaTeXCompiler with Docker fallback enabled (if no local latex)
DOCKER_IMAGE = os.getenv("LATEX_DOCKER_IMAGE", "texlive/texlive:latest")
compiler = LaTeXCompiler(use_docker_fallback=True, docker_image=DOCKER_IMAGE)

# Default LLM Transformer using server environment key
default_transformer = ResumeLLMTransformer()

class TailorRequest(BaseModel):
    resume: Resume = Field(..., description="The master resume structured JSON data.")
    job_description: str = Field(..., description="The target job description text to tailor the resume to.")

def remove_file(path: str):
    """Utility to clean up generated files after response is sent."""
    if os.path.exists(path):
        try:
            os.remove(path)
            logger.info(f"Cleaned up temporary file: {path}")
        except Exception as e:
            logger.warning(f"Could not remove temporary file {path}: {e}")

@app.get("/health", tags=["System"])
def health_check():
    """Simple API health check."""
    return {"status": "healthy", "service": "resume-etl-pipeline"}

@app.post("/compile/direct", response_class=FileResponse, tags=["Compilation"])
def compile_direct(resume: Resume, background_tasks: BackgroundTasks):
    """
    Directly compiles the provided structured resume data into a PDF.
    Bypasses AI transformation.
    """
    logger.info("Received direct compilation request")
    
    # 1. Render LaTeX template
    try:
        rendered_tex = renderer.render("resume_template.tex", resume)
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=422, detail=f"Template rendering failed: {str(e)}")

    # 2. Compile to PDF
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex
    temp_pdf_path = os.path.join(temp_dir, f"resume_{unique_id}.pdf")

    try:
        compiler.compile(rendered_tex, temp_pdf_path)
    except Exception as e:
        logger.error(f"Failed to compile PDF: {e}")
        remove_file(temp_pdf_path)
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {str(e)}")

    # 3. Schedule cleanup and return response
    background_tasks.add_task(remove_file, temp_pdf_path)
    return FileResponse(
        path=temp_pdf_path,
        media_type="application/pdf",
        filename=f"resume_{resume.personal_info.name.replace(' ', '_')}.pdf"
    )

@app.post("/compile/tailor", response_class=FileResponse, tags=["Compilation"])
def compile_tailor(
    request: TailorRequest, 
    background_tasks: BackgroundTasks,
    x_gemini_api_key: Optional[str] = Header(None, description="Optional Google Gemini API Key. If not provided, the server's environment key will be used.")
):
    """
    Tailors the resume to the provided Job Description using Gemini AI,
    renders the result to LaTeX, compiles it to PDF, and returns the PDF file.
    """
    logger.info("Received tailoring compilation request")
    
    # 1. Determine which transformer to use based on client-provided key
    if x_gemini_api_key:
        logger.info("Using client-provided Gemini API key from header")
        transformer = ResumeLLMTransformer(api_key=x_gemini_api_key)
    else:
        logger.info("Using default server environment Gemini API key")
        transformer = default_transformer

    # 2. Run Gemini AI Tailoring
    try:
        tailored_resume = transformer.tailor_resume(request.resume, request.job_description)
    except Exception as e:
        logger.error(f"Failed to tailor resume: {e}")
        raise HTTPException(status_code=502, detail=f"AI Tailoring failed: {str(e)}")

    # 3. Render LaTeX template
    try:
        rendered_tex = renderer.render("resume_template.tex", tailored_resume)
    except Exception as e:
        logger.error(f"Failed to render template: {e}")
        raise HTTPException(status_code=422, detail=f"Template rendering failed: {str(e)}")

    # 4. Compile to PDF
    temp_dir = tempfile.gettempdir()
    unique_id = uuid.uuid4().hex
    temp_pdf_path = os.path.join(temp_dir, f"resume_tailored_{unique_id}.pdf")

    try:
        compiler.compile(rendered_tex, temp_pdf_path)
    except Exception as e:
        logger.error(f"Failed to compile PDF: {e}")
        remove_file(temp_pdf_path)
        raise HTTPException(status_code=500, detail=f"LaTeX compilation failed: {str(e)}")

    # 5. Schedule cleanup and return response
    background_tasks.add_task(remove_file, temp_pdf_path)
    return FileResponse(
        path=temp_pdf_path,
        media_type="application/pdf",
        filename=f"resume_{request.resume.personal_info.name.replace(' ', '_')}_tailored.pdf"
    )
