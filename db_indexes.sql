
CREATE INDEX IF NOT EXISTS idx_perfume_brand_id ON perfume (brand_id);
CREATE INDEX IF NOT EXISTS idx_product_perfume_id ON product (perfume_id);
CREATE INDEX IF NOT EXISTS idx_product_is_active ON product (is_active);
CREATE INDEX IF NOT EXISTS idx_product_price ON product (price);
CREATE INDEX IF NOT EXISTS idx_product_type ON product (product_type);
CREATE INDEX IF NOT EXISTS idx_product_stock_quantity ON product (stock_quantity);

CREATE INDEX IF NOT EXISTS idx_perfume_concentration ON perfume (concentration);
CREATE INDEX IF NOT EXISTS idx_perfume_target_gender ON perfume (target_gender);
CREATE INDEX IF NOT EXISTS idx_perfume_recommended_season ON perfume (recommended_season);


CREATE INDEX IF NOT EXISTS idx_review_product_id ON review (product_id);
CREATE INDEX IF NOT EXISTS idx_review_user_id ON review (user_id);


CREATE INDEX IF NOT EXISTS idx_cart_item_cart_id ON cart_item (cart_id);
CREATE INDEX IF NOT EXISTS idx_customer_order_user_id ON customer_order (user_id);
CREATE INDEX IF NOT EXISTS idx_customer_order_status ON customer_order (status);
CREATE INDEX IF NOT EXISTS idx_order_item_order_id ON order_item (order_id);


CREATE INDEX IF NOT EXISTS idx_user_email ON user (email);


