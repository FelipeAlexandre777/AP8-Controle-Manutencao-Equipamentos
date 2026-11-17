import os
import sqlite3
from contextlib import closing
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.common import sign_payload

NODE_ID = os.getenv("NODE_ID", "controller-local")
DB_PATH = os.path.join(os.getenv("DATA_DIR", "."), f"{NODE_ID}.db")
os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
app = FastAPI(title=f"MineFleet Controller - {NODE_ID}", version="1.0.0")

class Command(BaseModel):
    vehicle_id: str = Field(min_length=2, max_length=30)
    action: str
    reason: str
    operation_id: str = Field(min_length=3, max_length=80)

def connect():
    return sqlite3.connect(DB_PATH)

def initialize():
    with closing(connect()) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS operations (
            operation_id TEXT PRIMARY KEY, vehicle_id TEXT NOT NULL,
            action TEXT NOT NULL, reason TEXT NOT NULL, result TEXT NOT NULL)""")
        db.commit()

initialize()

@app.get("/health")
def health():
    return {"node_id": NODE_ID, "status": "healthy"}

@app.post("/command")
def execute(command: Command):
    with closing(connect()) as db:
        row = db.execute("SELECT result FROM operations WHERE operation_id=?",
                         (command.operation_id,)).fetchone()
        if row:
            result = row[0]
        else:
            if command.action not in {"REDUCE_SPEED", "STOP_VEHICLE", "ISSUE_ALERT"}:
                raise HTTPException(status_code=400, detail="Ação não permitida")
            result = "ACCEPTED"
            db.execute("INSERT INTO operations VALUES (?, ?, ?, ?, ?)",
                       (command.operation_id, command.vehicle_id, command.action,
                        command.reason, result))
            db.commit()
    signed = {"node_id": NODE_ID, "operation_id": command.operation_id,
              "vehicle_id": command.vehicle_id, "action": command.action, "result": result}
    return {**signed, "signature": sign_payload(NODE_ID, signed)}
