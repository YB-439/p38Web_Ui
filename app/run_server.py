import os
import sys
import socket
import webbrowser
import threading
import time
import warnings

# Suppress scikit-learn version mismatch warning for clean startup
warnings.filterwarnings("ignore")

def is_port_available(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except socket.error:
            return False

def find_available_port(start_port: int = 8000, max_attempts: int = 10) -> int:
    for port in range(start_port, start_port + max_attempts):
        if is_port_available(port):
            return port
    return start_port

def open_browser_delayed(url: str, delay: float = 1.5):
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    import uvicorn
    
    # Ensure current directory is in sys.path
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)

    target_port = 8000
    if not is_port_available(target_port):
        print(f"[Notice] Port {target_port} is currently in use.")
        target_port = find_available_port(start_port=8001)
        print(f"[Notice] Selected available port: {target_port}")

    url = f"http://127.0.0.1:{target_port}"
    print("=" * 65)
    print("  p38α MAPK Activity & Applicability Domain Predictor Server")
    print(f"  Web Interface URL: {url}")
    print(f"  API Docs (Swagger): {url}/docs")
    print("=" * 65)
    print("  Starting Uvicorn engine... Press CTRL+C to stop.\n")

    # Open browser automatically in background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    uvicorn.run("app.main:app", host="127.0.0.1", port=target_port, reload=False, log_level="info")
