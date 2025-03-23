from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Source(BaseModel):
    title: str
    url: Optional[str] = None
    description: Optional[str] = None
    publication_date: Optional[date] = None
    
    class Config:
        orm_mode = True