# server/models/category.py
from pydantic import BaseModel
from typing import Optional

class Category(BaseModel):
    name: str
    color: Optional[str] = '#00D4FF'
    icon: Optional[str] = 'tool'

class CategoryUpdate(BaseModel):
    color: Optional[str] = None
    icon: Optional[str] = None
