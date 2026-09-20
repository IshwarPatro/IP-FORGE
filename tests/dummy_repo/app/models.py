"""
Dummy Repository: Models
Data transfer objects and entities for the e-commerce testbed.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class User(BaseModel):
    id: int
    email: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Product(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: str


class OrderItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class Order(BaseModel):
    id: int
    user_id: int
    items: List[OrderItem]
    total_amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
