import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    serial_port: str = Field(default=os.getenv("SERIAL_PORT", "/dev/ttyACM0"))
    baud: int = Field(default=int(os.getenv("BAUD", "115200")))
    simulate: bool = Field(default=os.getenv("SIMULATE", "false").lower() == "true")
    pi_native: bool = Field(default=os.getenv("PI_NATIVE", "false").lower() == "true")
    cors_origins: str = Field(default=os.getenv("CORS_ORIGINS", "http://localhost:5173"))

settings = Settings()
