<<<<<<< HEAD
# perfume
=======
# perfume — Fuad's package (cart / orders / reviews API)

This package adds the cart, checkout/orders, and product-review REST
endpoints on top of the base project from `perfume-Abir.zip`. It's built
to be dropped directly into that project — see `SETUP_INSTRUCTIONS.md`.

## Endpoints in this package

**Cart**
- `POST   /api/cart/add/` — add a product to the cart (`product_id`, `quantity`, optional `volume`)
- `GET    /api/cart/` — view the cart (items, quantities, line totals, subtotal, item count)
- `PATCH  /api/cart/update/{cart_item_id}/` — change a line's quantity
- `DELETE /api/cart/remove/{cart_item_id}/` — remove a line

**Orders**
- `POST /api/orders/checkout/` — turn the cart into an order (creates order + order items, deducts stock, clears cart)
- `GET  /api/orders/{order_id}/` — one order's full detail
- `GET  /api/orders/` — the logged-in customer's orders, paginated, optional `?status=`

**Reviews**
- `POST /api/reviews/` — submit a review (`product_id`, `rating` 1–5, `comment`)
- `GET  /api/reviews/?product_id=X` — a product's reviews + average rating

All cart/order endpoints require `Authorization: Bearer <access_token>`
from `POST /api/accounts/login/`. Reviews are public to browse (`GET`),
login-required to post.

See `SETUP_INSTRUCTIONS.md` for exactly which files this adds/replaces.
>>>>>>> e964cdd (Initial perfume platform project)
