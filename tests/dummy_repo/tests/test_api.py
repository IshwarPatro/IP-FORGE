"""
Dummy Repository Test Suite
Validates catalog browsing, stock deduction, and discount calculation.
"""

import pytest
from starlette.testclient import TestClient
from tests.dummy_repo.app.api import dummy_app, catalog_service


@pytest.fixture
def client():
    return TestClient(dummy_app)


def test_list_all_products(client):
    """Test retrieving complete product catalog."""
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert any(p["name"] == "Mechanical Keyboard" for p in data)


def test_get_product_by_id(client):
    """Test single product retrieval."""
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Mechanical Keyboard"


def test_create_order_success(client):
    """Test valid order creation with stock decrement and discount."""
    initial_stock = catalog_service.get_product_by_id(2).stock
    payload = {
        "user_id": 42,
        "items": [
            {"product_id": 2, "quantity": 2, "unit_price": 60.0}
        ],
        "discount_pct": 10.0
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 201
    order = response.json()
    assert order["user_id"] == 42
    # 2 * 60 = 120, minus 10% = 108.0
    assert order["total_amount"] == 108.0
    assert order["status"] == "confirmed"

    # Verify inventory updated
    updated_stock = catalog_service.get_product_by_id(2).stock
    assert updated_stock == initial_stock - 2


def test_create_order_insufficient_stock(client):
    """Test order failure when requesting quantity exceeding stock."""
    payload = {
        "user_id": 10,
        "items": [
            {"product_id": 3, "quantity": 9999, "unit_price": 450.0}
        ]
    }
    response = client.post("/orders", json=payload)
    assert response.status_code == 400
    assert "Insufficient stock" in response.json()["detail"]
