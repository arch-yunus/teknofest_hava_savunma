import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from threading import Thread
import uvicorn
import os

app = FastAPI(title="GökKalkan AI Command Center")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global set of active websocket connections
active_connections = set()

@app.websocket("/ws/radar")
async def websocket_radar_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    try:
        while True:
            # We just keep the connection alive. Data is pushed from the main loop!
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_radar_data(data: dict):
    if not active_connections:
        return
    message = json.dumps(data)
    for connection in list(active_connections):
        try:
            await connection.send_text(message)
        except Exception:
            active_connections.remove(connection)

def push_data_to_clients(data: dict):
    """
    Called from main.py's synchronous loop.
    We create a new event loop or use asyncio.run to ping the broadcast.
    Because uvicorn runs in its own event loop, we need a thread-safe way.
    """
    try:
        # Fast fire-and-forget broadcast via the running loop if possible
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_radar_data(data), loop)
        else:
            asyncio.run(broadcast_radar_data(data))
    except RuntimeError:
        # Get/create a loop if no current loop exists in this thread
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
