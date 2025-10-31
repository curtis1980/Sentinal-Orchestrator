# ============================================
# Sentinel Console - FastAPI Dashboard
# ============================================
import os, subprocess
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from datetime import datetime

# ---------------- Setup ----------------
load_dotenv()
app = FastAPI(title="Sentinel Console")
app.add_middleware(SessionMiddleware, secret_key="replace_with_secure_key")

app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

# ---------------- Version Manager ----------------
def safe_update_version_file():
    """Keeps VERSION file synced with latest git commit (safe auto-increment)."""
    repo_url = "https://github.com/curtis1980/Sentinel-Orchestrator"
    version_file = Path("VERSION")
    try:
        current_version = "v0.1.0"
        last_commit = None
        if version_file.exists():
            raw = version_file.read_text(encoding="utf-8").strip()
            parts = [p.strip() for p in raw.split("|")]
            if parts:
                current_version = parts[0]
            if len(parts) > 1 and parts[1]:
                last_commit = parts[1].split("/")[-1]

        latest_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode("utf-8").strip()
        )

        if latest_commit != last_commit:
            major, minor, patch = current_version.strip("v").split(".")
            new_version = f"v{major}.{minor}.{int(patch)+1}"
            commit_url = f"{repo_url}/commit/{latest_commit}"
            version_file.write_text(f"{new_version} | {commit_url}", encoding="utf-8")
    except Exception as e:
        print("⚠️ Version manager failed:", e)
        if not version_file.exists():
            version_file.write_text("v0.1.0", encoding="utf-8")

safe_update_version_file()

# ---------------- Config ----------------
APP_PASSWORD = os.getenv("SENTINEL_PASSWORD")
if not APP_PASSWORD:
    print("⚠️ SENTINEL_PASSWORD not found. Set it in .env or Render environment.")

# ---------------- Routes ----------------
@app.get("/", response_class=HTMLResponse)
async def login(request: Request):
    if request.session.get("authenticated"):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("dashboard.html", {"request": request, "auth": False})

@app.post("/login", response_class=HTMLResponse)
async def do_login(request: Request, password: str = Form(...)):
    if APP_PASSWORD and password == APP_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse(url="/dashboard", status_code=303)
    context = {"request": request, "auth": False, "error": "Incorrect password"}
    return templates.TemplateResponse("dashboard.html", context)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/")
    version_file = Path("VERSION")
    version_label, version_url = "v0.1.0", None
    if version_file.exists():
        raw = version_file.read_text(encoding="utf-8").strip()
        parts = [p.strip() for p in raw.split("|")]
        if parts:
            version_label = parts[0]
        if len(parts) > 1 and parts[1]:
            version_url = parts[1]

    now = datetime.now().strftime("%I:%M %p")
    context = {
        "request": request,
        "auth": True,
        "version_label": version_label,
        "version_url": version_url,
        "time": now
    }
    return templates.TemplateResponse("dashboard.html", context)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/")

# ---------------- Run ----------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
