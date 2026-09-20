"""
Dummy Repository: FastAPI Application & Endpoints
Exposes REST endpoints for the e-commerce testbed.
"""

from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from tests.dummy_repo.app.models import Product, Order, OrderItem
from tests.dummy_repo.app.services import ProductCatalogService, OrderProcessingService

dummy_app = FastAPI(title="Dummy Target Store API", version="1.0.0")

# Dependency Singletons
catalog_service = ProductCatalogService()
order_service = OrderProcessingService(catalog=catalog_service)


class CreateOrderRequest(BaseModel):
    user_id: int
    items: List[OrderItem]
    discount_pct: float = 0.0


@dummy_app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = Query(None, description="Optional category filter")):
    """Returns catalog inventory."""
    return catalog_service.get_all_products(category=category)


@dummy_app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int):
    """Fetches details for a single product."""
    product = catalog_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@dummy_app.post("/orders", response_model=Order, status_code=201)
def create_order(request: CreateOrderRequest):
    """Processes a new order, validates stock, and calculates total."""
    try:
        order = order_service.create_order(
            user_id=request.user_id,
            items=request.items,
            discount_pct=request.discount_pct
        )
        return order
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@dummy_app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int):
    """Fetches order by identifier."""
    order = order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
