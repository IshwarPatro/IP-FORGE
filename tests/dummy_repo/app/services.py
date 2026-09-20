"""
Dummy Repository: Business Services
Handles product catalog operations and order processing logic.
"""

from typing import List, Optional
from tests.dummy_repo.app.models import Product, Order, OrderItem
from tests.dummy_repo.app.utils import calculate_discount


class ProductCatalogService:
    """Service managing inventory and product lookups."""

    def __init__(self):
        self._inventory: List[Product] = [
            Product(id=1, name="Mechanical Keyboard", price=120.0, stock=15, category="peripherals"),
            Product(id=2, name="Wireless Mouse", price=60.0, stock=25, category="peripherals"),
            Product(id=3, name="4K Gaming Monitor", price=450.0, stock=8, category="displays"),
        ]

    def get_all_products(self, category: Optional[str] = None) -> List[Product]:
        """Retrieves list of products, optionally filtered by category."""
        if category:
            return [p for p in self._inventory if p.category.lower() == category.lower()]
        return self._inventory

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Finds a product by primary identifier."""
        for product in self._inventory:
            if product.id == product_id:
                return product
        return None

    def update_stock(self, product_id: int, quantity: int) -> bool:
        """Deducts stock when an order is placed."""
        product = self.get_product_by_id(product_id)
        if not product or product.stock < quantity:
            return False
        product.stock -= quantity
        return True


class OrderProcessingService:
    """Service handling validation, discounting, and order completion."""

    def __init__(self, catalog: ProductCatalogService):
        self.catalog = catalog
        self._orders: List[Order] = []
        self._order_id_seq: int = 1

    def create_order(self, user_id: int, items: List[OrderItem], discount_pct: float = 0.0) -> Order:
        """Validates stock, calculates final totals, and persists order."""
        total = 0.0
        # Validate and deduct stock
        for item in items:
            product = self.catalog.get_product_by_id(item.product_id)
            if not product:
                raise ValueError(f"Product ID {item.product_id} not found")
            if product.stock < item.quantity:
                raise ValueError(f"Insufficient stock for product {product.name}")
            total += item.unit_price * item.quantity

        if discount_pct > 0.0:
            total = calculate_discount(total, discount_pct)

        # Deduct inventory
        for item in items:
            self.catalog.update_stock(item.product_id, item.quantity)

        order = Order(
            id=self._order_id_seq,
            user_id=user_id,
            items=items,
            total_amount=round(total, 2),
            status="confirmed"
        )
        self._orders.append(order)
        self._order_id_seq += 1
        return order

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Retrieves order by order identifier."""
        for order in self._orders:
            if order.id == order_id:
                return order
        return None
