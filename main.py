from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import json
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# Load known IPs from ip_list.json
with open("ip_list.json", "r") as file:
    known_ips = set(json.load(file)["ips"])

# Load previously logged IPs (if file exists)
LOG_FILE = "logged_ips.json"
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as file:
        all_ips = set(json.load(file)["logged_ips"])
else:
    all_ips = set()

def save_ips():
    """Save logged IPs to a JSON file for persistence."""
    with open(LOG_FILE, "w") as file:
        json.dump({"logged_ips": list(all_ips)}, file, indent=4)

@app.get("/", response_class=HTMLResponse)
async def get_content(request: Request, gclid: str = None):
    ip = request.client.host

    if gclid:
        marked_ip = f"gclid_{ip}"
        if ip in all_ips:  # If IP was logged normally, remove it
            all_ips.discard(ip)
        all_ips.add(marked_ip)  # Store with gclid marker
    else:
        if f"gclid_{ip}" not in all_ips:  # Don't override if already marked
            all_ips.add(ip)

    save_ips()  # Save IPs to file

    if ip in known_ips:
        return templates.TemplateResponse("main.html", {"request": request})
    if gclid:
        return templates.TemplateResponse("main.html", {"request": request, "gclid": gclid})
    
    return templates.TemplateResponse("main.html", {"request": request})

@app.get("/all-ips/")
async def get_all_ips():
    return {"logged_ips": list(all_ips)}

@app.get("/{page_name}", response_class=HTMLResponse)
async def serve_page(request: Request, page_name: str):
    if page_name in ["contact.html"]:
        return templates.TemplateResponse(page_name, {"request": request})
    return HTMLResponse("Page Not Found", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
