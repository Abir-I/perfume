-- Sprint 6: Database Query Optimization
--
-- Every model in accounts/models.py has `managed = False`, so Django
-- never generates migrations for them — any index has to be added by
-- hand, directly in the database. These cover the columns actually
-- hit by WHERE/JOIN/ORDER BY across catalog, admin, reviews, cart, and
-- orders (see the queries in catalog/views.py, catalog/admin_views.py,
-- reviews/views.py, cart/views.py, orders/views.py).
--
-- Safe to re-run: every statement uses IF NOT EXISTS. Run this against
-- both the current MySQL database and, after the Sprint 6 migration,
-- the new PostgreSQL database (syntax is MySQL here — see the note at
-- the bottom for the Postgres equivalent).

-- catalog: filtering products by brand, active flag, price, type
CREATE INDEX IF NOT EXISTS idx_perfume_brand_id ON perfume (brand_id);
CREATE INDEX IF NOT EXISTS idx_product_perfume_id ON product (perfume_id);
CREATE INDEX IF NOT EXISTS idx_product_is_active ON product (is_active);
CREATE INDEX IF NOT EXISTS idx_product_price ON product (price);
CREATE INDEX IF NOT EXISTS idx_product_type ON product (product_type);
CREATE INDEX IF NOT EXISTS idx_product_stock_quantity ON product (stock_quantity);

-- catalog filters added in Sprint 5 (concentration/gender/season)
CREATE INDEX IF NOT EXISTS idx_perfume_concentration ON perfume (concentration);
CREATE INDEX IF NOT EXISTS idx_perfume_target_gender ON perfume (target_gender);
CREATE INDEX IF NOT EXISTS idx_perfume_recommended_season ON perfume (recommended_season);

-- reviews: fetching all reviews for a product, checking for a duplicate
CREATE INDEX IF NOT EXISTS idx_review_product_id ON review (product_id);
CREATE INDEX IF NOT EXISTS idx_review_user_id ON review (user_id);

-- cart / orders: looking up a user's cart, a cart's items, a user's orders
CREATE INDEX IF NOT EXISTS idx_cart_item_cart_id ON cart_item (cart_id);
CREATE INDEX IF NOT EXISTS idx_customer_order_user_id ON customer_order (user_id);
CREATE INDEX IF NOT EXISTS idx_customer_order_status ON customer_order (status);
CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON order_item (order_id);

-- login / auth
CREATE INDEX IF NOT EXISTS idx_user_email ON user (email);

-- NOTE on PostgreSQL: `CREATE INDEX IF NOT EXISTS` works the same way
-- in Postgres, but MySQL's `CREATE INDEX IF NOT EXISTS` support varies
-- by version (8.0+ is fine). If your MySQL version rejects the
-- IF NOT EXISTS clause, drop it and wrap each statement in a check
-- against information_schema.statistics instead, or just run once.
