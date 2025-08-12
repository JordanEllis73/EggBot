from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from .models import Status, SetpointIn, DamperIn, TelemetryOut
from .serial_io import ControllerIO
from .config import settings

app = FastAPI(title="Big Green Egg API")
io = ControllerIO()

# CORS for dev UI
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if origins:
    print(f"Origins: {origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@app.get("/status", response_model=Status)
async def get_status():
    return io.get_status()

@app.post("/setpoint")
async def set_setpoint(data: SetpointIn):
    print(f"Received data: {data}")
    io.set_setpoint(data.setpoint_c)
    return {"ok": True, "setpoint_c": data.setpoint_c}

@app.post("/damper")
async def set_damper(data: DamperIn):
    io.set_damper(data.damper_percent)
    return {"ok": True, "damper_percent": data.damper_percent}

@app.get("/telemetry", response_model=TelemetryOut)
async def telemetry():
    return {"points": io.get_telemetry()}
