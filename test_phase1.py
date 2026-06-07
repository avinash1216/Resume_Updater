import os
import json
import logging
from pathlib import Path
from app.models.schema import Resume
from app.services.renderer import LaTeXRenderer
from app.services.compiler import LaTeXCompiler

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TestPhase1")

def main():
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "app" / "data" / "master_resume.json"
    template_name = "resume_template.tex"
    output_pdf = project_root / "output" / "resume_test.pdf"

    logger.info("Loading master resume data...")
    if not data_path.exists():
        logger.error(f"Data file not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    # 1. Validate data against schema
    logger.info("Validating JSON against Pydantic schema...")
    try:
        resume = Resume(**raw_data)
        logger.info("Schema validation successful!")
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return

    # 2. Render LaTeX template
    logger.info("Rendering LaTeX template...")
    try:
        renderer = LaTeXRenderer(templates_dir=str(project_root / "templates"))
        rendered_tex = renderer.render(template_name, resume)
        logger.info("Rendering successful!")
        
        # Save a preview of the rendered .tex for debugging
        preview_tex_path = project_root / "output" / "resume_rendered.tex"
        os.makedirs(preview_tex_path.parent, exist_ok=True)
        with open(preview_tex_path, "w", encoding="utf-8") as f:
            f.write(rendered_tex)
        logger.info(f"Rendered LaTeX written to {preview_tex_path}")
    except Exception as e:
        logger.error(f"Template rendering failed: {e}")
        return

    # 3. Compile LaTeX to PDF
    logger.info("Compiling LaTeX to PDF...")
    try:
        # Note: We use the lightweight, fast texlive docker image 'paperist/texlive-ja:latest' 
        # or 'blang/latex:ubuntu' or 'texlive/texlive:latest'. Let's default to 'texlive/texlive:latest'
        # or 'paperist/debian-nd' which is super small and fast to download.
        # Actually, let's use 'texlive/texlive:latest' as it is the most standard.
        compiler = LaTeXCompiler(use_docker_fallback=True, docker_image="texlive/texlive:latest")
        output_path = compiler.compile(rendered_tex, str(output_pdf))
        logger.info(f"PDF compilation successful! Output saved at: {output_path}")
    except Exception as e:
        logger.error(f"PDF compilation failed: {e}")

if __name__ == "__main__":
    main()
