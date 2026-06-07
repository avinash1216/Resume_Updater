import os
import time
import json
import subprocess
import httpx
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "app" / "data" / "master_resume.json"
    output_pdf = project_root / "output" / "resume_api_test.pdf"

    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        resume_data = json.load(f)

    # 1. Start the FastAPI server locally in the background
    print("Starting FastAPI server locally...")
    server_process = subprocess.Popen(
        [str(project_root / ".venv" / "Scripts" / "uvicorn.exe"), "app.main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Give the server a few seconds to start
    time.sleep(3)

    try:
        # 2. Send request to endpoint
        print("Sending POST request to /compile/direct...")
        response = httpx.post("http://localhost:8000/compile/direct", json=resume_data, timeout=30.0)
        
        if response.status_code == 200:
            print("Successfully received PDF from API!")
            os.makedirs(output_pdf.parent, exist_ok=True)
            with open(output_pdf, "wb") as f:
                f.write(response.content)
            print(f"PDF saved to: {output_pdf}")
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error during API request: {e}")
    finally:
        # 3. Terminate the server process
        print("Stopping FastAPI server...")
        server_process.terminate()
        server_process.wait()
        print("FastAPI server stopped.")

if __name__ == "__main__":
    main()
