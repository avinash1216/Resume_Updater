import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

from app.models.schema import Resume
from app.services.llm_transformer import ResumeLLMTransformer
from app.services.renderer import LaTeXRenderer
from app.services.compiler import LaTeXCompiler

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("TestPhase3")

SAMPLE_JD = """
Senior Python Developer / AI Engineer
We are looking for a Senior Developer to build containerized APIs.
Required Skills:
- Extensive experience building microservices using FastAPI and Python.
- Integration of Generative AI / Large Language Models (LLMs) (specifically Google Gemini) into backend services.
- Containerization and orchestration with Docker and Kubernetes.
- Experience writing robust SQL and managing relational databases.
- Strong focus on clean code and automated testing.
"""

def main():
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "app" / "data" / "master_resume.json"
    output_pdf = project_root / "output" / "resume_tailored_test.pdf"

    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("\n" + "="*80)
        print("WARNING: GEMINI_API_KEY is not configured in your .env file!")
        print("Please edit F:\\Resume_Updater\\.env and replace 'your_api_key_here' with a valid key.")
        print("="*80 + "\n")
        return

    print("Loading master resume...")
    with open(data_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    resume = Resume(**raw_data)
    
    # 1. Run LLM Transformer
    print("Initializing Gemini Transformer...")
    transformer = ResumeLLMTransformer(api_key=api_key)
    
    try:
        print("Running resume tailoring against Job Description...")
        tailored_resume = transformer.tailor_resume(resume, SAMPLE_JD)
        print("Gemini tailoring completed successfully!")
    except Exception as e:
        print(f"Error during tailoring: {e}")
        return

    # 2. Print Comparison/Diff of bullet points
    print("\n" + "="*80)
    print("COMPARING ORIGINAL VS TAILORED BULLETS")
    print("="*80)
    for orig_exp, tail_exp in zip(resume.experience, tailored_resume.experience):
        print(f"\nCompany: {orig_exp.company} | Role: {orig_exp.role}")
        print("-" * 50)
        for i, (orig_b, tail_b) in enumerate(zip(orig_exp.bullets, tail_exp.bullets), 1):
            print(f"Bullet {i}:")
            print(f"  [-] {orig_b}")
            print(f"  [+] {tail_b}")
    print("="*80 + "\n")

    # 3. Render and compile to PDF
    print("Rendering tailored LaTeX...")
    renderer = LaTeXRenderer(templates_dir=str(project_root / "templates"))
    rendered_tex = renderer.render("resume_template.tex", tailored_resume)
    
    # Save a preview of the rendered .tex for debugging
    preview_tex_path = project_root / "output" / "resume_tailored_rendered.tex"
    with open(preview_tex_path, "w", encoding="utf-8") as f:
        f.write(rendered_tex)
    
    print("Compiling tailored PDF...")
    compiler = LaTeXCompiler(use_docker_fallback=True)
    try:
        compiler.compile(rendered_tex, str(output_pdf))
        print(f"Tailored PDF compiled successfully at: {output_pdf}")
    except Exception as e:
        print(f"PDF compilation failed: {e}")

if __name__ == "__main__":
    main()
