import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import subprocess
import time
import os

def main():
    print("[TEST RUNNER] Starting Flask server...")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["API_KEY"] = "my-super-secret-powerautomate-key-2026"
    proc = subprocess.Popen([sys.executable, "app.py"], env=env)

    try:
        # Wait for server to boot
        time.sleep(2)

        # Run test client
        print("[TEST RUNNER] Running test_client.py...")
        res = subprocess.run([sys.executable, "test_client.py"], env=env, capture_output=True, text=True, encoding="utf-8")
        print("STDOUT:\n", res.stdout)
        if res.stderr:
            print("STDERR:\n", res.stderr)
        
        if res.returncode != 0:
            print(f"[TEST RUNNER] Test failed with code {res.returncode}")
            sys.exit(res.returncode)
    finally:
        print("[TEST RUNNER] Stopping Flask server...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("[TEST RUNNER] Server stopped.")

if __name__ == "__main__":
    main()
