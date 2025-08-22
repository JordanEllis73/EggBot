from fastapi import APIRouter, HTTPException
from app.models.schemas import MeaterConnectIn, MeaterStatus, MeaterDeviceList
from app.meater_manager import meater_manager

router = APIRouter(prefix="/meater", tags=["meater"])


@router.get("/status", response_model=MeaterStatus)
async def get_meater_status():
    """Get current Meater probe status"""
    return meater_manager.get_status()


@router.post("/connect")
async def connect_meater(data: MeaterConnectIn):
    """Connect to Meater probe by Bluetooth address"""
    success = meater_manager.connect(data.address)
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to start connection - already connected or connecting"
        )
    return {"ok": True, "message": "Connection started", "address": data.address}


@router.post("/disconnect")
async def disconnect_meater():
    """Disconnect from Meater probe"""
    meater_manager.disconnect()
    return {"ok": True, "message": "Disconnected"}


@router.get("/scan", response_model=MeaterDeviceList)
async def scan_for_meater_devices():
    """Scan for available Meater devices"""
    devices = meater_manager.scan_for_devices()
    return {"devices": devices}


@router.post("/scan-and-connect")
async def scan_and_connect_meater():
    """Scan for Meater devices and connect to the first one found"""
    success = meater_manager.scan_and_connect()
    if not success:
        raise HTTPException(
            status_code=400, 
            detail="Failed to start scan - already connected, connecting, or scanning"
        )
    return {"ok": True, "message": "Scan and connect started"}