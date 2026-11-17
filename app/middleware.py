import asyncio
import json
import os
from collections import Counter
from contextlib import asynccontextmanager
import httpx
import paho.mqtt.client as mqtt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.common import verify_signature

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
CONTROLLERS = [x.strip() for x in os.getenv(
    "CONTROLLERS",
    "http://localhost:8101,http://localhost:8102,http://localhost:8103,http://localhost:8104"
).split(",") if x.strip()]
QUORUM = 3
telemetry_store = {}
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="minefleet-middleware")

class Command(BaseModel):
    vehicle_id: str = Field(min_length=2, max_length=30)
    action: str
    reason: str
    operation_id: str = Field(min_length=3, max_length=80)

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        client.subscribe("minefleet/sensors/telemetry", qos=1)

def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())
        if "vehicle_id" in data:
            telemetry_store[data["vehicle_id"]] = data
    except (ValueError, UnicodeDecodeError):
        return

@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    try:
        mqtt_client.connect(MQTT_HOST, 1883, 60)
        mqtt_client.loop_start()
    except OSError:
        pass
    yield
    mqtt_client.loop_stop()
    try:
        mqtt_client.disconnect()
    except Exception:
        pass

app = FastAPI(title="MineFleet Middleware", version="1.0.0", lifespan=lifespan)

@app.get("/")
def home():
    return {"project": "MineFleet", "role": "middleware",
            "replicas": len(CONTROLLERS), "quorum": QUORUM}

@app.get("/status")
async def status():
    async with httpx.AsyncClient(timeout=1.5) as client:
        checks = await asyncio.gather(
            *[client.get(url + "/health") for url in CONTROLLERS],
            return_exceptions=True)
    nodes = [{"controller": url, "available":
              not isinstance(response, Exception) and response.status_code == 200}
             for url, response in zip(CONTROLLERS, checks)]
    return {"middleware": "online", "quorum_required": QUORUM,
            "available_replicas": sum(n["available"] for n in nodes), "controllers": nodes}

@app.get("/telemetry")
def get_telemetry():
    return {"count": len(telemetry_store), "vehicles": telemetry_store}

@app.post("/commands")
async def execute_command(command: Command):
    payload = command.model_dump()
    async with httpx.AsyncClient(timeout=2.5) as client:
        responses = await asyncio.gather(
            *[client.post(url + "/command", json=payload) for url in CONTROLLERS],
            return_exceptions=True)
    valid, rejected = [], []
    for index, response in enumerate(responses):
        if isinstance(response, Exception) or response.status_code != 200:
            rejected.append({"controller": CONTROLLERS[index], "reason": "indisponível ou erro HTTP"})
            continue
        try:
            data = response.json()
            signed = {k: data[k] for k in
                      ("node_id", "operation_id", "vehicle_id", "action", "result")}
            if (data["operation_id"] != command.operation_id
                or data["vehicle_id"] != command.vehicle_id
                or data["action"] != command.action
                or not verify_signature(data["node_id"], signed, data["signature"])):
                rejected.append({"controller": CONTROLLERS[index],
                                 "reason": "assinatura ou conteúdo inválido"})
                continue
            valid.append(data)
        except (KeyError, ValueError, TypeError):
            rejected.append({"controller": CONTROLLERS[index], "reason": "resposta malformada"})
    votes = Counter((r["operation_id"], r["vehicle_id"], r["action"], r["result"]) for r in valid)
    winner, count = votes.most_common(1)[0] if votes else (None, 0)
    if count < QUORUM:
        raise HTTPException(status_code=503, detail={
            "message": "Quórum não atingido; operação não confirmada",
            "valid_responses": len(valid), "required": QUORUM, "rejected": rejected})
    result = {"operation_id": winner[0], "vehicle_id": winner[1],
              "action": winner[2], "result": winner[3]}
    mqtt_client.publish("minefleet/actuators/commands", json.dumps(result), qos=1)
    return {"confirmed": True, "quorum": f"{count}/{len(CONTROLLERS)}",
            "decision": result, "rejected_responses": rejected}
