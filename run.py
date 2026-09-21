import os
import sys
import re
import time
import subprocess
import webbrowser
import urllib.request

def wait_for_link_ready(url, max_attempts=20):
    print("Waiting for global DNS propagation...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    for _ in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status in (200, 302):
                    return True
        except Exception:
            time.sleep(1.5)
    return False

def main():
    print("=" * 65)
    print("                 PERDANGA ALLSHARE LAUNCHER")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Start Flask Backend
    print("\n[1/2] Starting Flask backend...")
    backend = subprocess.Popen(
        [sys.executable, "app.py"],
        cwd=base_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(1.5)

    # 2. Start Cloudflare Tunnel
    print("[2/2] Initializing Cloudflare Tunnel (HTTP/2)...")
    tunnel_cmd = ["cloudflared", "tunnel", "--protocol", "http2", "--url", "http://localhost:8080"]

    try:
        tunnel = subprocess.Popen(
            tunnel_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    except FileNotFoundError:
        print("\n[ERROR] 'cloudflared' not found! Make sure Cloudflared is installed.")
        backend.terminate()
        return

    url_regex = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    public_url = None

    print("Fetching secure tunnel link...")

    try:
        for line in iter(tunnel.stdout.readline, ''):
            if not line:
                break

            if not public_url:
                match = url_regex.search(line)
                if match:
                    public_url = match.group(0)

                    # Copy to Windows clipboard immediately
                    try:
                        subprocess.run("clip", input=public_url, text=True, check=False)
                    except Exception:
                        pass

                    # Wait until DNS is fully resolved worldwide
                    wait_for_link_ready(public_url)

                    print("\n" + "=" * 65)
                    print("                PERDANGA ALLSHARE IS LIVE!")
                    print("=" * 65)
                    print(f"\n  PUBLIC LINK (COPIED TO CLIPBOARD):\n  {public_url}\n")
                    print("  LOCAL DASHBOARD:\n  http://localhost:8080\n")
                    print("=" * 65)
                    print("  Opening ready link in your browser...")
                    print("  Press Ctrl+C to stop all services.")
                    print("=" * 65 + "\n")

                    webbrowser.open(public_url)

            if "Registered tunnel connection" in line:
                print("[INFO] Tunnel connected successfully to Cloudflare edge.")

    except KeyboardInterrupt:
        print("\nStopping services...")
    finally:
        tunnel.terminate()
        backend.terminate()
        try:
            tunnel.wait(timeout=2)
            backend.wait(timeout=2)
        except Exception:
            tunnel.kill()
            backend.kill()
        print("Done. All services closed cleanly.")

if __name__ == '__main__':
    main()