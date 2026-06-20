"""
Local Range Launcher for CyberThreatForge
Automatically checks dependencies, installs them if missing, starts the Uvicorn web server,
and launches the browser dashboard.
"""

import os
import sys
import subprocess
import time
import webbrowser

def check_dependencies():
    print("[*] Checking local environment dependencies...")
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        import jose
        print("[+] All dependencies met.")
    except ImportError:
        print("[-] Missing dependencies. Installing via requirements.txt...")
        req_path = os.path.join("backend", "requirements.txt")
        if not os.path.exists(req_path):
            print(f"[!] Error: Could not locate requirements file at {req_path}")
            sys.exit(1)
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])
            print("[+] Installation successful.")
        except subprocess.CalledProcessError as e:
            print(f"[!] Dependency installation failed: {e}")
            sys.exit(1)

def main():
    check_dependencies()
    
    # Set CWD to backend directory to resolve import paths cleanly
    backend_dir = os.path.join(os.getcwd(), "backend")
    if not os.path.exists(backend_dir):
        print(f"[!] Error: Backend directory not found at {backend_dir}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("STARTING CYBERTHREATFORGE WEB SERVER...")
    print("=" * 60)
    
    # Start uvicorn server in a subprocess
    server_process = None
    try:
        # Run uvicorn server using Python executable
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000"
        ]
        
        server_process = subprocess.Popen(
            cmd,
            cwd=backend_dir,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Wait for server startup
        print("[*] Waiting for server to initialize...")
        time.sleep(2)
        
        # Launch default browser
        target_url = "http://127.0.0.1:8000/"
        print(f"[+] Opening browser at {target_url}...")
        webbrowser.open(target_url)
        
        # Keep process alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n[*] Shutting down CyberThreatForge range server...")
        if server_process:
            server_process.terminate()
            server_process.wait()
        print("[+] Server stopped.")
        
if __name__ == "__main__":
    main()
