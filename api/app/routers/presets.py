from fastapi import APIRouter, HTTPException
from typing import List
import json
import os
from app.models.schemas import PIDPreset, SavePresetRequest

router = APIRouter(prefix="/pid-presets", tags=["presets"])

PRESETS_DIR = "pid_presets"
os.makedirs(PRESETS_DIR, exist_ok=True)

@router.get("/")
async def get_pid_presets():
    """Get list of available PID presets"""
    presets = []
    
    if os.path.exists(PRESETS_DIR):
        for filename in os.listdir(PRESETS_DIR):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(PRESETS_DIR, filename), 'r') as f:
                        preset_data = json.load(f)
                        presets.append({
                            "name": preset_data["name"],
                            "gains": preset_data["gains"]
                        })
                except Exception as e:
                    print(f"Error reading preset {filename}: {e}")
    
    return presets

@router.get("/{preset_name}")
async def load_pid_preset(preset_name: str):
    """Load a specific PID preset"""
    filename = f"{preset_name}.json"
    filepath = os.path.join(PRESETS_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Preset not found")
    
    try:
        with open(filepath, 'r') as f:
            preset_data = json.load(f)
        return {"gains": preset_data["gains"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading preset: {str(e)}")

@router.post("/")
async def save_pid_preset(request: SavePresetRequest):
    """Save a new PID preset"""

    if (os.path.exists(PRESETS_DIR)):
        filename = request.name
        if not filename.endswith('.json'):
            filename += '.json'
        print(filename)
            
        filepath = os.path.join(PRESETS_DIR, filename)
        with open(filepath, 'w') as json_file:
            req_dict = {"name" : request.name, "gains" : request.gains}
            json.dump(req_dict, json_file, indent=4) # indent=4 for pretty-printing
        return {"ok": True}
