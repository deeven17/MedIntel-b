from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
import os

from database import users_col

router = APIRouter()


SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-that-should-be-kept-secret")
ALGORITHM = "HS256"


class ConnectionManager:
  def __init__(self):
      # user_email -> list[WebSocket]
      self.user_connections: Dict[str, List[WebSocket]] = {}
      # admin connections (no per-email routing needed)
      self.admin_connections: List[WebSocket] = []

  async def connect(self, ws: WebSocket, role: str, email: str | None):
      await ws.accept()
      if role == "admin":
          self.admin_connections.append(ws)
      elif role == "user" and email:
          self.user_connections.setdefault(email, []).append(ws)

  def disconnect(self, ws: WebSocket):
      if ws in self.admin_connections:
          self.admin_connections.remove(ws)
      for email, conns in list(self.user_connections.items()):
          if ws in conns:
              conns.remove(ws)
          if not conns:
              self.user_connections.pop(email, None)

  async def notify_admins(self, payload: dict):
      dead: List[WebSocket] = []
      for ws in self.admin_connections:
          try:
              await ws.send_json(payload)
          except Exception:
              dead.append(ws)
      for ws in dead:
          self.disconnect(ws)

  async def notify_user(self, email: str, payload: dict):
      conns = self.user_connections.get(email, [])
      dead: List[WebSocket] = []
      for ws in conns:
          try:
              await ws.send_json(payload)
          except Exception:
              dead.append(ws)
      for ws in dead:
          self.disconnect(ws)


manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket):
  """
  WebSocket for real-time notifications.

  Expects query params:
  - token: JWT access token
  - role: "admin" | "user"
  """
  token = websocket.query_params.get("token")
  role = websocket.query_params.get("role", "user")

  if not token:
      await websocket.close()
      return

  try:
      payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
      email = payload.get("sub")
      if not email:
          await websocket.close()
          return
      # Optional: enforce admin role for admin connections
      if role == "admin" and payload.get("role") != "admin":
          await websocket.close()
          return
  except JWTError:
      await websocket.close()
      return

  await manager.connect(websocket, role=role, email=email)

  try:
      while True:
          # We don't expect messages from client; just keep connection alive
          await websocket.receive_text()
  except WebSocketDisconnect:
      manager.disconnect(websocket)


async def notify_admins_event(event_type: str, data: dict):
  """
  Helper for other routes to notify all admins.
  """
  await manager.notify_admins({"type": event_type, "data": data})


async def notify_user_event(user_email: str, event_type: str, data: dict):
  """
  Helper to notify a specific user.
  """
  await manager.notify_user(user_email, {"type": event_type, "data": data})

