from typing import List, Optional
from pydantic import BaseModel, Field

class ProblemItem(BaseModel):
    name: str
    count: Optional[int] = Field(None, description="Count if shown else None")
    maude_link: Optional[str] = Field(None, description="Direct link into MAUDE for this problem")

class DeviceResult(BaseModel):
    device_name: str
    device_url: str
    device_problems: List[ProblemItem]
    patient_problems: List[ProblemItem]

class ScrapeResponse(BaseModel):
    query: dict
    min_year: int
    results: List[DeviceResult]
