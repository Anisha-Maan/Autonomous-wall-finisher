# backend/models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class RectObstacle(BaseModel):
    x: float = Field(..., ge=0)   # bottom-left x in meters
    y: float = Field(..., ge=0)   # bottom-left y in meters
    w: float = Field(..., gt=0)   # width in meters
    h: float = Field(..., gt=0)   # height in meters

class WallSpec(BaseModel):
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    brush_width: float = Field(0.05, gt=0)   # default 5cm
    resolution: float = Field(0.02, gt=0)    # grid resolution default 2cm
    obstacles: List[RectObstacle] = []

class PlanRequest(BaseModel):
    wall: WallSpec
    name: Optional[str] = None
