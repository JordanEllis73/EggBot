import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import presets, controller, telemetry, meater, pi_native
from app.config import settings

app = FastAPI(
    title="Big Green Egg API",
    description="Pi-Native EggBot Controller"
)

app.include_router(presets.router)
app.include_router(controller.router)
app.include_router(telemetry.router)
app.include_router(meater.router)
app.include_router(pi_native.router)

print("Pi-native controller enabled")

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
