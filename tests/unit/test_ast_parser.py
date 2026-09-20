"""
Unit tests for the AST Parser.
"""

from pathlib import Path
from forge.rag.ast_parser import ASTParser, ASTSymbol


def test_ast_parser_extracts_dummy_repo_symbols():
    """Verify ASTParser extracts classes, functions, and signatures from dummy_repo."""
    parser = ASTParser()
    repo_path = Path("tests/dummy_repo")
    summaries = parser.parse_directory(repo_path)

    assert len(summaries) >= 4  # models.py, utils.py, services.py, api.py

    # Collect all symbols
    all_symbols = [sym for s in summaries for sym in s.symbols]
    symbol_names = [s.name for s in all_symbols]

    # Verify classes
    assert "User" in symbol_names
    assert "Product" in symbol_names
    assert "Order" in symbol_names
    assert "ProductCatalogService" in symbol_names
    assert "OrderProcessingService" in symbol_names

    # Verify methods
    assert "create_order" in symbol_names
    assert "get_product_by_id" in symbol_names
    assert "calculate_discount" in symbol_names

    # Verify signature extraction
    create_order_sym = next(s for s in all_symbols if s.name == "create_order")
    assert create_order_sym.symbol_type == "method"
    assert create_order_sym.parent_class == "OrderProcessingService"
    assert "user_id: int" in create_order_sym.signature
    assert "discount_pct: float" in create_order_sym.signature
    assert "-> Order" in create_order_sym.signature
    assert create_order_sym.docstring is not None
    assert "Validates stock" in create_order_sym.docstring

    # Verify utils function
    calc_discount_sym = next(s for s in all_symbols if s.name == "calculate_discount")
    assert calc_discount_sym.symbol_type == "function"
    assert "price: float" in calc_discount_sym.signature
    assert "-> float" in calc_discount_sym.signature
