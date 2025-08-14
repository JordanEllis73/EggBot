from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import Status, SetpointIn, DamperIn, PIDGainsIn
from app.dependencies import get_controller
from app.serial_io import ControllerIO

router = APIRouter(prefix="", tags=["controller"])

@router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

@router.get("/status", response_model=Status)
async def get_status(controller: ControllerIO = Depends(get_controller)):
    return controller.get_status()

@router.post("/setpoint")
async def set_setpoint(data: SetpointIn, controller: ControllerIO = Depends(get_controller)):
    print(f"Received data: {data}")
    controller.set_setpoint(data.setpoint_c)
    return {"ok": True, "setpoint_c": data.setpoint_c}

@router.post("/damper")
async def set_damper(data: DamperIn, controller: ControllerIO = Depends(get_controller)):
    await controller.set_damper(data.damper_percent)
    return {"ok": True, "damper_percent": data.damper_percent}

@router.post("/pid_gains")
async def set_pid_gains(data: PIDGainsIn, controller: ControllerIO = Depends(get_controller)):
    controller.set_pid_gains(*data.pid_gains)
    return {"ok": True, "pid_gains": data.pid_gains}
