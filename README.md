<div align="center">

<h1 align="center">Perdanga AllShare</h1>

<p align="center">
  <b>P2P file sharing platform powered by Flask and Cloudflare Tunnel.</b>
</p>

<br/>

<img src="https://github.com/PerdangaSoftware/Perdanga-AllShare/blob/main/screenshots/Perdanga%20AllShare.png?raw=true" width="540" alt="Perdanga AllShare Interface Preview"/>

</div>


## Highlights & Features

- **Cloud Tunneling:** Instant public encrypted access via Cloudflare without port forwarding, dynamic DNS, or static IPs.
- **Multi-Stream Uploads:** Parallel HTTP/2 worker pool saturates available upstream bandwidth.
- **PIN-Protected Deletion:** Server-enforced PIN verification (`8159`) prevents unauthorized file removal.
- **Path Traversal Hardening:** Strict canonical path validation restricts operations exclusively to safe directories.
- **Automated Launcher:** Verifies global DNS propagation, copies URL to clipboard, and opens your browser in one click.


## Technology Stack

- **Core Backend:** Python 3.9+, Flask, Werkzeug WSGI.
- **Networking & Transport:** Cloudflare Tunnel (`cloudflared`), HTTP/2 transport protocol.
- **Frontend Architecture:** Vanilla JavaScript (ES6+), Fetch API, Asynchronous XMLHttpRequest with progress monitoring, CSS3 Design Tokens.
- **Security & Integrity:** Canonical path verification, custom HTTP response security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`), server-side PIN authentication.
- **Automation & Process Control:** Windows Batch, Python Process Management (`subprocess`, `urllib`, `re`).


## Project Structure

```text
PerdangaAllShare/
├── templates/
│   └── index.html           # Minimalist frontend template with drag-and-drop UI
│
├── uploads/                 # Local directory for stored public files
│
├── temp/                    # Staging buffer for in-flight chunk assemblies
│
├── app.py                   # Core Flask server, multi-thread assembler & security routes
├── run.py                   # Process controller, DNS readiness checker & clipboard handler
├── start_allshare.bat       # Master one-click startup launcher for Windows
├── requirements.txt         # Python package dependencies
└── README.md                # Project documentation
```

---

## Getting Started

### Prerequisites

1. **Windows 10 / 11 (64-bit)**
2. **Python 3.9+** (added to system `PATH`)
3. **Cloudflare Tunnel CLI (`cloudflared`)** installed:
   ```cmd
   winget install --id Cloudflare.cloudflared
   ```

---

### Installation & Setup

1. Clone the repository:
   ```cmd
   git clone https://github.com/YOUR_USERNAME/perdanga-allshare.git
   cd perdanga-allshare
   ```

2. Install backend dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

3. Launch the platform:
   ```cmd
   start_allshare.bat
   ```

The launcher will automatically:
- Start the Flask backend in the background.
- Initialize the Cloudflare Tunnel over HTTP/2.
- Poll and verify worldwide DNS propagation.
- Copy the public encrypted URL directly to your clipboard.
- Open the ready interface in your default web browser.

<br>

<div align="center">
  <h2>Perdanga Forever!</h2>
</div>
