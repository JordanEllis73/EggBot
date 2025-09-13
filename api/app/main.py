import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from app.routers import presets, controller, telemetry, meater
from app.config import settings

# Try to include Pi-native router if available
try:
    from app.routers import pi_native
    PI_NATIVE_AVAILABLE = True
except ImportError:
    PI_NATIVE_AVAILABLE = False

app = FastAPI(
    title="Big Green Egg API", 
    description="Pi-Native Enhanced EggBot Controller" if PI_NATIVE_AVAILABLE else "EggBot Controller"
)

app.include_router(presets.router)
app.include_router(controller.router)
app.include_router(telemetry.router)
app.include_router(meater.router)

# Include Pi-native enhanced endpoints if available
if PI_NATIVE_AVAILABLE:
    app.include_router(pi_native.router)
    print("Pi-native enhanced endpoints enabled")

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
