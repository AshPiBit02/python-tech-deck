# E-Commerce API with Domain Exceptions

A small e-commerce API split into independent resource routers
(products, inventory, orders), using custom domain exceptions instead
of scattered `HTTPException` calls, with a shared DB engine managed
by the app's lifespan.

## Structure

```
ecommerce_api/
├── main.py                 # lifespan wiring, exception handlers, router mounting
├── database.py              # FakeDBEngine + lifespan context manager
├── exceptions.py             # OutOfStockError, InvalidCouponError, OrderNotFoundError
├── models.py                  # shared Pydantic schemas
└── routers/
    ├── products.py             # /products
    ├── inventory.py             # /inventory  (owns reserve_stock())
    └── orders.py                  # /orders  (composes products + inventory + coupons)
```

## Why domain exceptions instead of `HTTPException`

`reserve_stock()` in `inventory.py` and `_validate_coupon()` in
`orders.py` never import `HTTPException` or think about status codes.
They raise `OutOfStockError` / `InvalidCouponError` — plain Python
exceptions that describe what went wrong in business terms. `main.py`
registers exactly one handler per exception type:

| Exception | Raised when | HTTP response |
|---|---|---|
| `OutOfStockError` | An order requests more units than are in stock | `409` with `product_id`, `requested`, `available` |
| `InvalidCouponError` | A coupon code doesn't exist/isn't valid | `400` with the offending `code` |
| `OrderNotFoundError` | Looking up an order that doesn't exist | `404` with the `order_id` |

Benefits:
- **Consistency** — every place that can run out of stock (today just
  `orders.py`, but could later be a "reserve for cart" endpoint, a
  background job, etc.) gets the exact same response shape for free.
- **Testability** — business logic can be unit-tested by asserting an
  exception type is raised, with no HTTP client or app instance needed.
- **Separation of concerns** — routers describe *what* went wrong;
  `main.py` is the only place that decides *how* that becomes HTTP.

Routine "not found" lookups that aren't business rules (e.g. GET
`/products/{id}` for an ID that was never created) stay as plain
`HTTPException` calls — domain exceptions are reserved for rules that
matter to the business.

## Lifespan-managed DB engine

`database.py` defines a `FakeDBEngine` standing in for a real
SQLAlchemy `AsyncEngine` or connection pool. It's created **once**, in
`lifespan()`, when the app starts — not per request — and stored on
`app.state`. The `get_db_engine` dependency hands routes that same
shared instance; `orders.py`'s `create_order` takes it as a dependency
to show where a real `INSERT` would happen.

## Running it

```bash
pip install fastapi uvicorn
uvicorn main:app --reload
```

Docs: `http://localhost:8000/docs`

## Try it out

```bash
# List seeded products
curl http://localhost:8000/products/

# Successful order (10% off with a valid coupon)
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 2}], "coupon_code": "SAVE10"}'

# InvalidCouponError -> 400
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 1, "quantity": 1}], "coupon_code": "FAKECODE"}'
# {"error":"invalid_coupon","code":"FAKECODE","detail":"Invalid coupon 'FAKECODE': Coupon is invalid or expired"}

# OutOfStockError -> 409 (product 2 only has 15 in stock)
curl -X POST http://localhost:8000/orders/ \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 2, "quantity": 9999}]}'
# {"error":"out_of_stock","product_id":2,"requested":9999,"available":15,"detail":"..."}

# OrderNotFoundError -> 404
curl http://localhost:8000/orders/999
# {"error":"order_not_found","order_id":999,"detail":"Order 999 not found"}
```

## Notes

- Storage is in-memory per router — restart clears everything. Swap
  `FakeDBEngine` for a real async engine and the routers for real
  queries without changing the exception/handler pattern at all.
- `orders.py` imports `reserve_stock` from `inventory.py` and
  `_products_db` from `products.py` directly, since all three run in
  the same process — a real service might instead call them over an
  internal API or repository layer, but the domain-exception pattern
  stays identical either way.