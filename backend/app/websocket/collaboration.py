# backend/app/websocket/collaboration.py
import socketio

# Async Socket.IO server for real‑time collaboration
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio)

@sio.event
async def connect(sid, environ):
    print(f"🔗 Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"🔌 Client disconnected: {sid}")

@sio.on('action')
async def handle_action(sid, data):
    # Broadcast the action to all other peers
    await sio.emit('action', data, skip_sid=sid)
