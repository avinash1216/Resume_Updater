import os
import time
import json
import subprocess
import httpx
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent
    data_path = project_root / "app" / "data" / "master_resume.json"
    output_pdf = project_root / "output" / "resume_docker_api_test.pdf"

    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        resume_data = json.load(f)

    # 1. Start the Docker container
    print("Starting FastAPI containerized server...")
    # Clean up any old container with the same name if it exists
    subprocess.run(["docker", "rm", "-f", "resume-etl-test-container"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    start_cmd = [
        "docker", "run", "-d",
        "--name", "resume-etl-test-container",
        "-p", "8000:8000",
        "resume-etl-pipeline:latest"
    ]
    
    container_proc = subprocess.run(start_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if container_proc.returncode != 0:
        print(f"Error starting container: {container_proc.stderr}")
        return
        
    container_id = container_proc.stdout.strip()
    print(f"Container started. ID: {container_id[:12]}")

    # Poll /health until server is ready (up to 10 seconds)
    print("Waiting for server to become healthy...")
    server_ready = False
    for i in range(10):
        try:
            res = httpx.get("http://localhost:8000/health", timeout=1.0)
            if res.status_code == 200:
                print("Server is healthy and ready!")
                server_ready = True
                break
        except Exception:
            pass
        time.sleep(1)
        
    if not server_ready:
        print("Error: Server failed to start up within 10 seconds.")
        # print logs before failing
        print("=== CONTAINER LOGS ===")
        logs_proc = subprocess.run(["docker", "logs", "resume-etl-test-container"], stdout=subprocess.PIPE, text=True)
        print(logs_proc.stdout)
        print("======================")
        # cleanup
        subprocess.run(["docker", "rm", "-f", "resume-etl-test-container"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    try:
        # 2. Send request to endpoint
        print("Sending POST request to container /compile/direct...")
        response = httpx.post("http://localhost:8000/compile/direct", json=resume_data, timeout=30.0)
        
        if response.status_code == 200:
            print("Successfully received PDF from containerized API!")
            os.makedirs(output_pdf.parent, exist_ok=True)
            with open(output_pdf, "wb") as f:
                f.write(response.content)
            print(f"PDF saved to: {output_pdf}")
        else:
            print(f"Error: Container API returned status code {response.status_code}")
            print(response.text)
            
            # Print container logs to debug
            print("=== CONTAINER LOGS ===")
            logs_proc = subprocess.run(["docker", "logs", "resume-etl-test-container"], stdout=subprocess.PIPE, text=True)
            print(logs_proc.stdout)
            print("======================")
            
    except Exception as e:
        print(f"Error during API request: {e}")
    finally:
        # 3. Stop and remove the container
        print("Stopping and removing container...")
        subprocess.run(["docker", "rm", "-f", "resume-etl-test-container"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("Container cleaned up.")

if __name__ == "__main__":
    main()
