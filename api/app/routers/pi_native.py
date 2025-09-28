"""
Enhanced API endpoints for Pi-native functionality
Provides access to multi-probe monitoring, advanced PID features, and system diagnostics
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Dict, Any

from app.models.schemas import (
    SystemStatus, ProbeStatus, PIDTuningInfo, PIDPresetLoad, 
    ProbeCalibration, PerformanceStats, EnhancedTelemetryOut,
    TelemetryPoint
)
from app.dependencies import get_controller, ControllerIO

router = APIRouter(prefix="/pi", tags=["pi-native"])

def get_pi_controller(controller=Depends(get_controller)) -> ControllerIO:
    """Dependency to get pi-native controller (always available now)"""
    return controller

@router.get("/system/status", response_model=SystemStatus)
async def get_system_status(controller: ControllerIO = Depends(get_pi_controller)):
    """Get comprehensive system status including all probes"""
    try:
        system_status = controller.get_system_status()
        
        # Convert probe status to Pydantic models
        probes_dict = {}
        for probe_name, status in system_status["probes"].items():
            probes_dict[probe_name] = ProbeStatus(**status)
        
        return SystemStatus(
            probes=probes_dict,
            system_enabled=system_status["system_enabled"],
            safety_shutdown=system_status["safety_shutdown"],
            control_loop_count=system_status["control_loop_count"],
            telemetry_points=system_status["telemetry_points"],
            connected_probes=system_status["connected_probes"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")

@router.get("/probes/status")
async def get_probe_status(controller: ControllerIO = Depends(get_pi_controller)):
    """Get status of all temperature probes"""
    try:
        return controller.get_probe_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get probe status: {str(e)}")

@router.get("/temperatures")
async def get_all_temperatures(controller: ControllerIO = Depends(get_pi_controller)):
    """Get current temperatures from all connected probes"""
    try:
        status = controller.get_enhanced_status()
        return {
            "pit_temp_c": status.get("pit_temp_c"),
            "meat_temp_1_c": status.get("meat_temp_1_c"),
            "meat_temp_2_c": status.get("meat_temp_2_c"),
            "ambient_temp_c": status.get("ambient_temp_c"),
            "connected_probes": status.get("connected_probes", []),
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get temperatures: {str(e)}")

@router.get("/telemetry/enhanced", response_model=EnhancedTelemetryOut)
async def get_enhanced_telemetry(controller: ControllerIO = Depends(get_pi_controller)):
    """Get enhanced telemetry data with all temperature probes"""
    try:
        telemetry_data = controller.get_enhanced_telemetry()
        
        # Convert to TelemetryPoint models
        points = []
        for point in telemetry_data:
            points.append(TelemetryPoint(**point))
        
        return EnhancedTelemetryOut(points=points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get enhanced telemetry: {str(e)}")

@router.post("/telemetry/clear")
async def clear_telemetry(controller: ControllerIO = Depends(get_pi_controller)):
    """Clear all telemetry data"""
    try:
        controller.clear_telemetry()
        return {"ok": True, "message": "Telemetry data cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear telemetry: {str(e)}")

@router.get("/pid/tuning-info", response_model=PIDTuningInfo)
async def get_pid_tuning_info(controller: ControllerIO = Depends(get_pi_controller)):
    """Get PID tuning information for manual tuning"""
    try:
        tuning_info = controller.get_pid_tuning_info()
        return PIDTuningInfo(**tuning_info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PID tuning info: {str(e)}")

@router.get("/pid/presets")
async def get_pid_presets(controller: ControllerIO = Depends(get_pi_controller)):
    """Get list of available PID presets"""
    try:
        presets = controller.get_available_presets()
        return {"presets": presets}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PID presets: {str(e)}")

@router.post("/pid/preset/load")
async def load_pid_preset(
    data: PIDPresetLoad, 
    controller: ControllerIO = Depends(get_pi_controller)
):
    """Load a PID tuning preset"""
    try:
        controller.load_pid_preset(data.preset_name)
        gains = controller.controller.get_pid_gains()
        return {
            "ok": True, 
            "preset_loaded": data.preset_name,
            "gains": {
                "kp": gains[0],
                "ki": gains[1], 
                "kd": gains[2]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load PID preset: {str(e)}")

@router.post("/probes/calibrate")
async def calibrate_probe(
    data: ProbeCalibration,
    controller: ControllerIO = Depends(get_pi_controller)
):
    """Calibrate a temperature probe using known actual temperature"""
    try:
        controller.calibrate_probe(data.probe_name, data.actual_temperature)
        return {
            "ok": True,
            "probe_calibrated": data.probe_name,
            "actual_temperature": data.actual_temperature
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calibrate probe: {str(e)}")

@router.get("/system/performance", response_model=PerformanceStats)
async def get_performance_stats(controller: ControllerIO = Depends(get_pi_controller)):
    """Get system performance statistics"""
    try:
        stats = controller.get_performance_stats()
        return PerformanceStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance stats: {str(e)}")

@router.post("/safety/reset")
async def reset_safety_shutdown(controller: ControllerIO = Depends(get_pi_controller)):
    """Reset safety shutdown after resolving issues"""
    try:
        controller.reset_safety_shutdown()
        return {"ok": True, "message": "Safety shutdown reset"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reset safety shutdown: {str(e)}")

@router.get("/safety/status")
async def get_safety_status(controller: ControllerIO = Depends(get_pi_controller)):
    """Get safety system status"""
    try:
        status = controller.get_enhanced_status()
        return {
            "safety_shutdown": status.get("safety_shutdown", False),
            "system_enabled": controller.controller.is_running(),
            "control_mode": status.get("control_mode", "manual"),
            "pit_temp_c": status.get("pit_temp_c"),
            "setpoint_c": status.get("setpoint_c"),
            "connected_probes": status.get("connected_probes", []),
            "timestamp": datetime.now().isoformat() + "Z"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get safety status: {str(e)}")

@router.get("/debug/controller-info")
async def get_controller_debug_info(controller: ControllerIO = Depends(get_pi_controller)):
    """Get debug information about the controller (development use)"""
    try:
        return {
            "controller_type": "ControllerIO",
            "controller_running": controller.controller.is_running(),
            "performance_stats": controller.get_performance_stats(),
            "probe_status": controller.get_probe_status(),
            "enhanced_status": controller.get_enhanced_status()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get debug info: {str(e)}")

# Backwards compatibility endpoints
@router.get("/status")
async def get_status_legacy(controller: ControllerIO = Depends(get_pi_controller)):
    """Legacy status endpoint with enhanced data"""
    return controller.get_status()

@router.get("/telemetry")  
async def get_telemetry_legacy(controller: ControllerIO = Depends(get_pi_controller)):
    """Legacy telemetry endpoint"""
    return {"points": controller.get_telemetry()}