import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class LaTeXCompiler:
    def __init__(self, use_docker_fallback: bool = True, docker_image: str = "texlive/texlive:latest"):
        self.use_docker_fallback = use_docker_fallback
        self.docker_image = docker_image

    def compile(self, latex_content: str, output_pdf_path: str) -> str:
        """
        Compiles the LaTeX content and saves the generated PDF to output_pdf_path.
        Returns the path to the compiled PDF if successful.
        """
        output_pdf_path = os.path.abspath(output_pdf_path)
        output_dir = os.path.dirname(output_pdf_path)
        os.makedirs(output_dir, exist_ok=True)

        # Create a temporary compilation directory inside the project to facilitate reliable Docker mounts
        project_root = Path(__file__).resolve().parent.parent.parent
        temp_dir = project_root / "temp_build"

        tex_filename = "resume.tex"
        pdf_filename = "resume.pdf"
        tex_filepath = temp_dir / tex_filename
        compiled_pdf_filepath = temp_dir / pdf_filename

        # Clean any old intermediate build files in temp_dir to prevent corruption
        self._cleanup(temp_dir, keep_pdf=False)

        # Re-create the temp directory if it was deleted
        os.makedirs(temp_dir, exist_ok=True)

        # Write the LaTeX content to the temporary file
        with open(tex_filepath, "w", encoding="utf-8") as f:
            f.write(latex_content)

        success = False
        error_msg = ""

        # Step 1: Try local pdflatex
        try:
            logger.info("Attempting local LaTeX compilation...")
            result = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_filename],
                cwd=str(temp_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            if result.returncode == 0:
                logger.info("Local compilation succeeded!")
                success = True
            else:
                error_msg = f"pdflatex exited with code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                logger.warning(f"Local compilation failed: {error_msg}")
        except FileNotFoundError:
            logger.warning("Local pdflatex binary not found.")
            error_msg = "Local pdflatex not found on PATH."

        # Step 2: Try Docker fallback if local failed and fallback is enabled
        if not success and self.use_docker_fallback:
            logger.info("Attempting Docker-based LaTeX compilation...")
            # We must use absolute paths for docker mounts
            abs_temp_dir = os.path.abspath(temp_dir)
            
            # Format volume mount path for Windows Docker
            # e.g., F:\Resume_Updater\temp_build -> /workspace
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{abs_temp_dir}:/workspace",
                "-w", "/workspace",
                self.docker_image,
                "pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_filename
            ]
            
            try:
                result = subprocess.run(
                    docker_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                if result.returncode == 0:
                    logger.info("Docker compilation succeeded!")
                    success = True
                else:
                    error_msg = f"Docker pdflatex exited with code {result.returncode}.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
                    logger.error(f"Docker compilation failed: {error_msg}")
            except Exception as e:
                error_msg = f"Failed to execute Docker command: {e}"
                logger.error(error_msg)

        if success and os.path.exists(compiled_pdf_filepath):
            # Copy the output PDF to the final destination
            shutil.copy2(compiled_pdf_filepath, output_pdf_path)
            logger.info(f"Successfully wrote output PDF to {output_pdf_path}")
            # Cleanup intermediate build files but keep the PDF in case they want it (we clean it on next run)
            self._cleanup(temp_dir, keep_pdf=True)
            return output_pdf_path
        else:
            self._cleanup(temp_dir, keep_pdf=False)
            raise RuntimeError(f"LaTeX Compilation Failed:\n{error_msg}")

    def _cleanup(self, temp_dir: Path, keep_pdf: bool = False):
        """Cleans up auxiliary files in the compilation directory."""
        extensions = [".aux", ".log", ".out", ".tex"]
        if not keep_pdf:
            extensions.append(".pdf")
            
        for ext in extensions:
            filepath = temp_dir / f"resume{ext}"
            if filepath.exists():
                try:
                    os.remove(filepath)
                except Exception as e:
                    logger.warning(f"Could not remove temporary file {filepath}: {e}")
                    
        # Also clean up standard temp_dir folder if empty
        if not keep_pdf:
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
