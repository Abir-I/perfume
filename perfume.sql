-- ============================================================
--  PERFUME RETAIL & DECANTING PLATFORM — DATABASE SCHEMA
--  MySQL 8.0+
--  Generated: June 2026
-- ============================================================

DROP DATABASE IF EXISTS perfume_platform;
CREATE DATABASE perfume_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE perfume_platform;

-- ============================================================
-- 1. ROLE
-- ============================================================
CREATE TABLE role (
    role_id     INT           NOT NULL AUTO_INCREMENT,
    role_name   VARCHAR(50)   NOT NULL UNIQUE,        -- 'admin', 'customer'
    PRIMARY KEY (role_id)
);

-- ============================================================
-- 2. USER
-- ============================================================
CREATE TABLE user (
    user_id       INT            NOT NULL AUTO_INCREMENT,
    role_id       INT            NOT NULL,
    first_name    VARCHAR(100)   NOT NULL,
    last_name     VARCHAR(100)   NOT NULL,
    email         VARCHAR(255)   NOT NULL UNIQUE,
    password_hash VARCHAR(255)   NOT NULL,
    phone         VARCHAR(20),
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active     TINYINT(1)     NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_user_role FOREIGN KEY (role_id) REFERENCES role(role_id)
);

-- ============================================================
-- 3. ADDRESS
-- ============================================================
CREATE TABLE address (
    address_id    INT           NOT NULL AUTO_INCREMENT,
    user_id       INT           NOT NULL,
    address_line1 VARCHAR(255)  NOT NULL,
    address_line2 VARCHAR(255),
    city          VARCHAR(100)  NOT NULL,
    state         VARCHAR(100),
    postal_code   VARCHAR(20),
    country       VARCHAR(100)  NOT NULL DEFAULT 'Bangladesh',
    is_default    TINYINT(1)    NOT NULL DEFAULT 0,
    PRIMARY KEY (address_id),
    CONSTRAINT fk_address_user FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 4. BRAND
-- ============================================================
CREATE TABLE brand (
    brand_id          INT           NOT NULL AUTO_INCREMENT,
    brand_name        VARCHAR(150)  NOT NULL UNIQUE,
    country_of_origin VARCHAR(100),
    description       TEXT,
    PRIMARY KEY (brand_id)
);

-- ============================================================
-- 5. PERFUME
-- ============================================================
CREATE TABLE perfume (
    perfume_id         INT           NOT NULL AUTO_INCREMENT,
    brand_id           INT           NOT NULL,
    perfume_name       VARCHAR(200)  NOT NULL,
    concentration      ENUM('EDT','EDP','Parfum','EDC','Cologne') NOT NULL,
    top_notes          VARCHAR(255),
    middle_notes       VARCHAR(255),
    base_notes         VARCHAR(255),
    longevity_hours    DECIMAL(4,1),
    sillage            ENUM('Intimate','Moderate','Strong','Enormous'),
    recommended_season ENUM('Spring','Summer','Fall','Winter','All Season'),
    target_gender      ENUM('Male','Female','Unisex') NOT NULL,
    description        TEXT,
    image_url          VARCHAR(500),
    created_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (perfume_id),
    CONSTRAINT fk_perfume_brand FOREIGN KEY (brand_id) REFERENCES brand(brand_id)
);

-- ============================================================
-- 6. BULK_BOTTLE  (inventory of original bottles purchased)
-- ============================================================
CREATE TABLE bulk_bottle (
    bottle_id             INT             NOT NULL AUTO_INCREMENT,
    perfume_id            INT             NOT NULL,
    batch_number          VARCHAR(100)    NOT NULL UNIQUE,
    purchase_date         DATE            NOT NULL,
    bottle_size_ml        DECIMAL(8,2)    NOT NULL,   -- e.g. 100.00
    ml_remaining          DECIMAL(8,2)    NOT NULL,   -- tracks usage
    cost_price            DECIMAL(10,2)   NOT NULL,
    supplier_name         VARCHAR(200),
    authenticity_verified TINYINT(1)      NOT NULL DEFAULT 0,
    verification_notes    TEXT,
    PRIMARY KEY (bottle_id),
    CONSTRAINT fk_bottle_perfume FOREIGN KEY (perfume_id) REFERENCES perfume(perfume_id),
    CONSTRAINT chk_ml_remaining CHECK (ml_remaining >= 0)
);

-- ============================================================
-- 7. PRODUCT  (what appears in the store — full bottle OR decant)
-- ============================================================
CREATE TABLE product (
    product_id     INT             NOT NULL AUTO_INCREMENT,
    perfume_id     INT             NOT NULL,
    product_type   ENUM('full_bottle','decant') NOT NULL,
    volume_ml      DECIMAL(8,2)    NOT NULL,          -- 5, 10, 20, 100, etc.
    price          DECIMAL(10,2)   NOT NULL,
    stock_quantity INT             NOT NULL DEFAULT 0,
    is_active      TINYINT(1)      NOT NULL DEFAULT 1,
    created_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    CONSTRAINT fk_product_perfume FOREIGN KEY (perfume_id) REFERENCES perfume(perfume_id),
    CONSTRAINT chk_stock CHECK (stock_quantity >= 0),
    CONSTRAINT chk_price CHECK (price > 0)
);

-- ============================================================
-- 8. DECANT_BATCH  (traceability: which bottle → which product)
-- ============================================================
CREATE TABLE decant_batch (
    decant_batch_id  INT       NOT NULL AUTO_INCREMENT,
    bottle_id        INT       NOT NULL,
    product_id       INT       NOT NULL,
    quantity_created INT       NOT NULL,
    quantity_sold    INT       NOT NULL DEFAULT 0,
    date_created     DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by       INT       NOT NULL,              -- admin user_id
    notes            TEXT,
    PRIMARY KEY (decant_batch_id),
    CONSTRAINT fk_decant_bottle  FOREIGN KEY (bottle_id)  REFERENCES bulk_bottle(bottle_id),
    CONSTRAINT fk_decant_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT fk_decant_user    FOREIGN KEY (created_by) REFERENCES user(user_id),
    CONSTRAINT chk_qty_sold CHECK (quantity_sold <= quantity_created)
);

-- ============================================================
-- 9. CART
-- ============================================================
CREATE TABLE cart (
    cart_id    INT      NOT NULL AUTO_INCREMENT,
    user_id    INT      NOT NULL UNIQUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_id),
    CONSTRAINT fk_cart_user FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE CASCADE
);

-- ============================================================
-- 10. CART_ITEM
-- ============================================================
CREATE TABLE cart_item (
    cart_item_id INT      NOT NULL AUTO_INCREMENT,
    cart_id      INT      NOT NULL,
    product_id   INT      NOT NULL,
    quantity     INT      NOT NULL DEFAULT 1,
    added_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_item_id),
    UNIQUE KEY uq_cart_product (cart_id, product_id),
    CONSTRAINT fk_cartitem_cart    FOREIGN KEY (cart_id)    REFERENCES cart(cart_id)    ON DELETE CASCADE,
    CONSTRAINT fk_cartitem_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT chk_cart_qty CHECK (quantity > 0)
);

-- ============================================================
-- 11. ORDER
-- ============================================================
CREATE TABLE `order` (
    order_id      INT             NOT NULL AUTO_INCREMENT,
    user_id       INT             NOT NULL,
    address_id    INT             NOT NULL,
    order_date    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status        ENUM('Pending','Confirmed','Processing','Shipped','Delivered','Cancelled')
                                  NOT NULL DEFAULT 'Pending',
    total_amount  DECIMAL(12,2)   NOT NULL,
    notes         TEXT,
    PRIMARY KEY (order_id),
    CONSTRAINT fk_order_user    FOREIGN KEY (user_id)    REFERENCES user(user_id),
    CONSTRAINT fk_order_address FOREIGN KEY (address_id) REFERENCES address(address_id)
);

-- ============================================================
-- 12. ORDER_ITEM
-- ============================================================
CREATE TABLE order_item (
    order_item_id INT            NOT NULL AUTO_INCREMENT,
    order_id      INT            NOT NULL,
    product_id    INT            NOT NULL,
    quantity      INT            NOT NULL,
    unit_price    DECIMAL(10,2)  NOT NULL,
    subtotal      DECIMAL(12,2)  GENERATED ALWAYS AS (quantity * unit_price) STORED,
    PRIMARY KEY (order_item_id),
    CONSTRAINT fk_orderitem_order   FOREIGN KEY (order_id)   REFERENCES `order`(order_id),
    CONSTRAINT fk_orderitem_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT chk_order_qty CHECK (quantity > 0)
);

-- ============================================================
-- 13. PAYMENT
-- ============================================================
CREATE TABLE payment (
    payment_id     INT             NOT NULL AUTO_INCREMENT,
    order_id       INT             NOT NULL UNIQUE,
    payment_date   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    payment_method ENUM('Cash','bKash','Nagad','Card','Bank Transfer') NOT NULL,
    amount         DECIMAL(12,2)   NOT NULL,
    transaction_id VARCHAR(200),
    status         ENUM('Pending','Completed','Failed','Refunded') NOT NULL DEFAULT 'Pending',
    PRIMARY KEY (payment_id),
    CONSTRAINT fk_payment_order FOREIGN KEY (order_id) REFERENCES `order`(order_id)
);

-- ============================================================
-- 14. INVOICE
-- ============================================================
CREATE TABLE invoice (
    invoice_id     INT             NOT NULL AUTO_INCREMENT,
    order_id       INT             NOT NULL UNIQUE,
    invoice_number VARCHAR(50)     NOT NULL UNIQUE,
    issued_date    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_amount   DECIMAL(12,2)   NOT NULL,
    tax_amount     DECIMAL(10,2)   NOT NULL DEFAULT 0.00,
    status         ENUM('Draft','Issued','Paid','Cancelled') NOT NULL DEFAULT 'Issued',
    PRIMARY KEY (invoice_id),
    CONSTRAINT fk_invoice_order FOREIGN KEY (order_id) REFERENCES `order`(order_id)
);

-- ============================================================
-- 15. REVIEW
-- ============================================================
CREATE TABLE review (
    review_id           INT       NOT NULL AUTO_INCREMENT,
    user_id             INT       NOT NULL,
    product_id          INT       NOT NULL,
    rating              TINYINT   NOT NULL,
    comment             TEXT,
    created_at          DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_verified_purchase TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY uq_user_product_review (user_id, product_id),
    PRIMARY KEY (review_id),
    CONSTRAINT fk_review_user    FOREIGN KEY (user_id)    REFERENCES user(user_id),
    CONSTRAINT fk_review_product FOREIGN KEY (product_id) REFERENCES product(product_id),
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5)
);

-- ============================================================
-- 16. CHATBOT_LOG
-- ============================================================
CREATE TABLE chatbot_log (
    log_id       INT          NOT NULL AUTO_INCREMENT,
    user_id      INT,                                  -- nullable: guest users
    session_id   VARCHAR(100) NOT NULL,
    user_message TEXT         NOT NULL,
    bot_response TEXT         NOT NULL,
    timestamp    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (log_id),
    CONSTRAINT fk_chatlog_user FOREIGN KEY (user_id) REFERENCES user(user_id)
        ON DELETE SET NULL
);

-- ============================================================
-- INDEXES  (for performance on common query patterns)
-- ============================================================
CREATE INDEX idx_perfume_brand        ON perfume(brand_id);
CREATE INDEX idx_product_perfume      ON product(perfume_id);
CREATE INDEX idx_product_type         ON product(product_type);
CREATE INDEX idx_bulkbottle_perfume   ON bulk_bottle(perfume_id);
CREATE INDEX idx_decant_bottle        ON decant_batch(bottle_id);
CREATE INDEX idx_decant_product       ON decant_batch(product_id);
CREATE INDEX idx_order_user           ON `order`(user_id);
CREATE INDEX idx_order_status         ON `order`(status);
CREATE INDEX idx_orderitem_order      ON order_item(order_id);
CREATE INDEX idx_review_product       ON review(product_id);
CREATE INDEX idx_chatlog_session      ON chatbot_log(session_id);
CREATE INDEX idx_chatlog_user         ON chatbot_log(user_id);

-- ============================================================
-- VIEWS
-- ============================================================

-- Full product details with perfume & brand info
CREATE VIEW vw_product_catalog AS
SELECT
    p.product_id,
    p.product_type,
    p.volume_ml,
    p.price,
    p.stock_quantity,
    pf.perfume_name,
    pf.concentration,
    pf.top_notes,
    pf.middle_notes,
    pf.base_notes,
    pf.longevity_hours,
    pf.recommended_season,
    pf.target_gender,
    b.brand_name,
    b.country_of_origin
FROM product p
JOIN perfume pf ON p.perfume_id = pf.perfume_id
JOIN brand   b  ON pf.brand_id  = b.brand_id
WHERE p.is_active = 1;

-- Decant traceability: each decant product traced to its source bottle
CREATE VIEW vw_decant_traceability AS
SELECT
    db.decant_batch_id,
    db.date_created,
    db.quantity_created,
    db.quantity_sold,
    (db.quantity_created - db.quantity_sold) AS quantity_available,
    p.product_id,
    p.volume_ml AS decant_volume_ml,
    p.price     AS decant_price,
    pf.perfume_name,
    b.brand_name,
    bb.bottle_id,
    bb.batch_number,
    bb.bottle_size_ml,
    bb.ml_remaining,
    bb.authenticity_verified,
    u.first_name AS created_by_first,
    u.last_name  AS created_by_last
FROM decant_batch db
JOIN product     p   ON db.product_id   = p.product_id
JOIN bulk_bottle bb  ON db.bottle_id    = bb.bottle_id
JOIN perfume     pf  ON bb.perfume_id   = pf.perfume_id
JOIN brand       b   ON pf.brand_id     = b.brand_id
JOIN user        u   ON db.created_by   = u.user_id;

-- Order summary with customer and payment info
CREATE VIEW vw_order_summary AS
SELECT
    o.order_id,
    o.order_date,
    o.status         AS order_status,
    o.total_amount,
    u.user_id,
    u.first_name,
    u.last_name,
    u.email,
    pay.payment_method,
    pay.status       AS payment_status,
    inv.invoice_number
FROM `order` o
JOIN user    u   ON o.user_id   = u.user_id
LEFT JOIN payment pay ON o.order_id = pay.order_id
LEFT JOIN invoice inv ON o.order_id = inv.order_id;

-- Average rating per product
CREATE VIEW vw_product_ratings AS
SELECT
    product_id,
    COUNT(*)          AS review_count,
    ROUND(AVG(rating), 2) AS avg_rating
FROM review
GROUP BY product_id;

-- ============================================================
-- SAMPLE DATA
-- ============================================================

-- Roles
INSERT INTO role (role_name) VALUES ('admin'), ('customer');

-- Users
INSERT INTO user (role_id, first_name, last_name, email, password_hash, phone) VALUES
(1, 'Abir',    'Hossain',  'abir@perfumeco.com',    '$2b$12$admin_hash_placeholder',   '01700000001'),
(2, 'Rafi',    'Islam',    'rafi@gmail.com',         '$2b$12$customer_hash_placeholder', '01800000002'),
(2, 'Nadia',   'Sultana',  'nadia@gmail.com',        '$2b$12$customer_hash_placeholder', '01800000003');

-- Addresses
INSERT INTO address (user_id, address_line1, city, country, is_default) VALUES
(2, 'House 12, Road 5, Dhanmondi', 'Dhaka', 'Bangladesh', 1),
(3, 'Flat 3B, Mirpur-10',          'Dhaka', 'Bangladesh', 1);

-- Brands
INSERT INTO brand (brand_name, country_of_origin) VALUES
('Dior',        'France'),
('Tom Ford',    'USA'),
('Creed',       'France'),
('Versace',     'Italy'),
('Armani',      'Italy');

-- Perfumes
INSERT INTO perfume (brand_id, perfume_name, concentration, top_notes, middle_notes, base_notes,
                     longevity_hours, sillage, recommended_season, target_gender) VALUES
(1, 'Sauvage',            'EDP', 'Bergamot, Pepper',    'Lavender, Star Anise', 'Ambroxan, Cedar',         8.0, 'Strong',   'All Season', 'Male'),
(2, 'Black Orchid',       'EDP', 'Black Truffle, Ylang','Black Orchid, Jasmine','Sandalwood, Vanilla',     7.0, 'Strong',   'Winter',     'Unisex'),
(3, 'Aventus',            'EDP', 'Blackcurrant, Apple', 'Jasmine, Rose',        'Musk, Oakmoss',           9.0, 'Enormous', 'All Season', 'Male'),
(4, 'Eros',               'EDT', 'Lemon, Apple, Mint',  'Tonka Bean, Geranium', 'Vanilla, Vetiver, Oakmoss',6.0,'Moderate', 'Spring',     'Male'),
(5, 'Acqua di Gio',       'EDT', 'Calabrian Bergamot',  'Jasmine, Rosemary',    'Patchouli, White Musk',   5.0, 'Moderate', 'Summer',     'Male');

-- Bulk Bottles (inventory)
INSERT INTO bulk_bottle (perfume_id, batch_number, purchase_date, bottle_size_ml, ml_remaining,
                         cost_price, supplier_name, authenticity_verified) VALUES
(1, 'BTL-2026-001', '2026-06-01', 100.00, 80.00, 6500.00, 'Global Fragrance Imports', 1),
(2, 'BTL-2026-002', '2026-06-01', 100.00, 95.00, 9000.00, 'Global Fragrance Imports', 1),
(3, 'BTL-2026-003', '2026-06-05', 120.00, 120.00, 12000.00,'Prestige Perfumes BD',    1),
(4, 'BTL-2026-004', '2026-06-10', 100.00, 100.00, 5500.00, 'Global Fragrance Imports', 1),
(5, 'BTL-2026-005', '2026-06-10', 100.00, 100.00, 5000.00, 'Prestige Perfumes BD',    1);

-- Products (sellable listings)
INSERT INTO product (perfume_id, product_type, volume_ml, price, stock_quantity) VALUES
-- Sauvage
(1, 'decant',      5.00,   350.00, 4),
(1, 'decant',     10.00,   650.00, 2),
(1, 'full_bottle',100.00, 8500.00, 0),
-- Black Orchid
(2, 'decant',      5.00,   450.00, 1),
(2, 'decant',     10.00,   800.00, 0),
-- Aventus
(3, 'decant',      5.00,   600.00, 4),
(3, 'decant',     10.00,  1100.00, 2),
(3, 'decant',     20.00,  2000.00, 1),
-- Eros
(4, 'decant',      5.00,   280.00, 2),
(4, 'decant',     10.00,   520.00, 2),
-- Acqua di Gio
(5, 'decant',      5.00,   250.00, 3),
(5, 'decant',     10.00,   480.00, 3);

-- Decant Batches (traceability records)
INSERT INTO decant_batch (bottle_id, product_id, quantity_created, quantity_sold, date_created, created_by) VALUES
(1, 1,  4, 0, '2026-06-03', 1),   -- Sauvage 5ml from BTL-001
(1, 2,  2, 0, '2026-06-03', 1),   -- Sauvage 10ml from BTL-001
(2, 4,  1, 0, '2026-06-04', 1),   -- Black Orchid 5ml from BTL-002
(3, 6,  4, 0, '2026-06-07', 1),   -- Aventus 5ml from BTL-003
(3, 7,  2, 0, '2026-06-07', 1),   -- Aventus 10ml from BTL-003
(3, 8,  1, 0, '2026-06-07', 1),   -- Aventus 20ml from BTL-003
(4, 9,  2, 0, '2026-06-11', 1),   -- Eros 5ml from BTL-004
(4, 10, 2, 0, '2026-06-11', 1),   -- Eros 10ml from BTL-004
(5, 11, 3, 0, '2026-06-11', 1),   -- Acqua di Gio 5ml from BTL-005
(5, 12, 3, 0, '2026-06-11', 1);   -- Acqua di Gio 10ml from BTL-005

-- Cart & Cart Items
INSERT INTO cart (user_id) VALUES (2), (3);

INSERT INTO cart_item (cart_id, product_id, quantity) VALUES
(1, 1, 2),   -- Rafi: 2x Sauvage 5ml
(1, 6, 1),   -- Rafi: 1x Aventus 5ml
(2, 11, 1);  -- Nadia: 1x Acqua di Gio 5ml

-- Orders
INSERT INTO `order` (user_id, address_id, status, total_amount) VALUES
(2, 1, 'Delivered', 1250.00),
(3, 2, 'Processing', 480.00);

-- Order Items
INSERT INTO order_item (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 350.00),   -- 2x Sauvage 5ml
(1, 9, 1, 550.00),   -- 1x Eros 5ml (historical price)
(2, 12, 1, 480.00);  -- 1x Acqua di Gio 10ml

-- Payments
INSERT INTO payment (order_id, payment_method, amount, transaction_id, status) VALUES
(1, 'bKash',  1250.00, 'BK20260601-001', 'Completed'),
(2, 'Nagad',   480.00, 'NG20260615-002', 'Completed');

-- Invoices
INSERT INTO invoice (order_id, invoice_number, total_amount, tax_amount, status) VALUES
(1, 'INV-2026-0001', 1250.00, 0.00, 'Paid'),
(2, 'INV-2026-0002',  480.00, 0.00, 'Paid');

-- Reviews
INSERT INTO review (user_id, product_id, rating, comment, is_verified_purchase) VALUES
(2, 1, 5, 'Amazing scent, very long lasting. Will order again!', 1),
(2, 9, 4, 'Great fresh scent for daily wear.', 1);

-- Chatbot Logs
INSERT INTO chatbot_log (user_id, session_id, user_message, bot_response) VALUES
(2,   'sess-abc-001', 'What perfumes do you recommend for summer?',
       'For summer I recommend Acqua di Gio and Versace Eros EDT — both are fresh and moderate in projection.'),
(NULL, 'sess-xyz-002', 'Do you have Dior Sauvage decants?',
       'Yes! We currently have Dior Sauvage EDP available in 5ml and 10ml decants. Would you like to add one to your cart?');

-- ============================================================
-- END OF SCHEMA
-- ============================================================
