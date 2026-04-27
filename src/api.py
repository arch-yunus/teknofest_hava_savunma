import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="ARGUS UI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

active_connections = []

# Global Command Queue for Python backend to read
frontend_commands = []

from typing import Optional

class CommandRequest(BaseModel):
    action: str
    target_id: Optional[str] = None

# Serve static files (HTML, JS, CSS)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.websocket("/ws/radar")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text() # we don't necessarily expect text from client yet
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.post("/api/command")
async def receive_command(cmd: CommandRequest):
    """Frontend'den gelen manuel komutları sıraya ekler."""
    allowed = [
        "force_swarm", "toggle_auto_fire", "trigger_emp", 
        "toggle_weather", "toggle_radar_emission",
        "set_stage_1", "set_stage_2", "set_stage_3", # TEKNOFEST Stages
        "trigger_estop", "release_estop",            # E-Stop
        "toggle_manual_mode",                        # Mode Switch
        "force_hypersonic"                           # Phase 10 Hypersonic
    ]
    if cmd.action in allowed:
        frontend_commands.append({"action": cmd.action, "target_id": cmd.target_id})
        return {"status": "success", "action_queued": cmd.action}
    return {"status": "error", "message": "Unknown command"}

main_loop = None

def push_data_to_clients(data: dict):
    if not active_connections:
        return
    
    global main_loop
    json_data = json.dumps(data)
    
    async def _send():
        for connection in active_connections:
            try:
                await connection.send_text(json_data)
            except Exception:
                pass

    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(lambda: asyncio.create_task(_send()))
    else:
        # Fallback if loop not captured yet or not running
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(_send(), loop)
            else:
                loop.run_until_complete(_send())
        except: pass

@app.on_event("startup")
async def startup_event():
    global main_loop
    main_loop = asyncio.get_running_loop()

def start_server(host="0.0.0.0", port=8000):
    """
    Starts the FastAPI uvicorn server in a blocking manner.
    Should be called inside a Thread from main.py.
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    uvicorn.run(app, host=host, port=port, log_level="error")
