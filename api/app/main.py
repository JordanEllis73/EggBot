import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import presets, controller, telemetry
from app.serial_io import ControllerIO
from app.config import settings

app = FastAPI(title="Big Green Egg API")

app.include_router(presets.router)
app.include_router(controller.router)
app.include_router(telemetry.router)

# # CORS for dev UI
# origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
# if origins:
#     print(f"Origins: {origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
