from fastapi import APIRouter, Depends
from app.models.schemas import TelemetryOut
from app.dependencies import get_controller
from app.serial_io import ControllerIO

router = APIRouter(prefix="", tags=["telemetry"])


@router.get("/telemetry", response_model=TelemetryOut)
async def telemetry(controller: ControllerIO = Depends(get_controller)):
    return await {"points": controller.get_telemetry()}
