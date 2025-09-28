import os
from pydantic import BaseModel, Field

class Settings(BaseModel):
    simulate: bool = Field(default=os.getenv("SIMULATE", "false").lower() == "true")
    cors_origins: str = Field(default=os.getenv("CORS_ORIGINS", "http://localhost:5173"))

settings = Settings()
