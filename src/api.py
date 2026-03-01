import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

app = FastAPI(title="GökKalkan UI Server")

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

class CommandRequest(BaseModel):
    action: str

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
    if cmd.action in ["force_swarm", "toggle_auto_fire", "trigger_emp"]:
        frontend_commands.append(cmd.action)
        return {"status": "success", "action_queued": cmd.action}
    return {"status": "error", "message": "Unknown command"}

def push_data_to_clients(data: dict):
    """Called from main.py thread to push data to all connected ws clients"""
    if not active_connections:
        return
    
    json_data = json.dumps(data)
    
    async def _send():
        for connection in active_connections:
            try:
                await connection.send_text(json_data)
            except Exception:
                pass
                
    # Create new event loop for this thread if needed, or use existing
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(_send(), loop)
        else:
            loop.run_until_complete(_send())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(broadcast_radar_data(data))

def start_server(host="0.0.0.0", port=8000):
    """
    Starts the FastAPI uvicorn server in a blocking manner.
    Should be called inside a Thread from main.py.
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    if os.path.exists(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
    uvicorn.run(app, host=host, port=port, log_level="error")
