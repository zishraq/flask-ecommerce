DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS product;
DROP TABLE IF EXISTS product_tags;
DROP TABLE IF EXISTS product_by_tag;
DROP TABLE IF EXISTS product_wishlist;
DROP TABLE IF EXISTS shopping_cart;
DROP TABLE IF EXISTS shopping_cart_info;
DROP TABLE IF EXISTS products_by_cart;
DROP TABLE IF EXISTS product_by_cart;
DROP TABLE IF EXISTS shipper;
DROP TABLE IF EXISTS order_info;

DROP TABLE IF EXISTS shopping_cart_info;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS carts_by_orders;
DROP TABLE IF EXISTS shipping;

CREATE TABLE user (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  name TEXT,
  email TEXT UNIQUE,
  phone TEXT UNIQUE,
  role TEXT,
  address TEXT,
  joined_at TIMESTAMP
);

CREATE TABLE product (
    product_id TEXT PRIMARY KEY,
    product_name TEXT,
    description TEXT,
    product_category TEXT,
    price FLOAT,
    discount FLOAT ,
    created_at TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP,
    updated_by TEXT,
    in_stock INTEGER,
    total_sold INTEGER,
    FOREIGN KEY (created_by) REFERENCES user(username),
    FOREIGN KEY (updated_by) REFERENCES user(username)
);

CREATE TABLE product_tags (
    tag_name TEXT,
    created_at TIMESTAMP,
    created_by TEXT ,
    PRIMARY KEY (tag_name),
    FOREIGN KEY (created_by) REFERENCES user(username)
);

CREATE TABLE product_by_tag (
    tag_name TEXT,
    product_id TEXT,
    PRIMARY KEY (tag_name, product_id),
    FOREIGN KEY (tag_name) REFERENCES product_tags(tag_name),
    FOREIGN key (product_id) REFERENCES product(product_id)
);

CREATE TABLE product_wishlist (
    username TEXT,
    product_id TEXT,
    PRIMARY KEY (username, product_id),
    FOREIGN key (product_id) REFERENCES product(product_id),
    FOREIGN KEY (username) REFERENCES user(username)
);

CREATE TABLE shopping_cart_info (
    cart_id TEXT,
    username TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY(cart_id),
    FOREIGN KEY (username) REFERENCES user(username)
);

CREATE TABLE product_by_cart (
    cart_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    added_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY(cart_id, product_id),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart_info(cart_id),
    FOREIGN KEY (product_id) REFERENCES product(product_id)
);

CREATE TABLE shipper (
    shipper_id TEXT,
    shipper_name TEXT,
    phone_number TEXT,
    created_at TIMESTAMP,
    created_by TEXT,
    PRIMARY KEY(shipper_id)
);

CREATE TABLE order_info (
    order_id TEXT,
    created_at TIMESTAMP,
    payment_method TEXT,
    address TEXT,
    shipper_id TEXT,
    date_shipped TIMESTAMP,
    shipment_created_by TEXT,
    PRIMARY KEY(order_id),
    FOREIGN KEY (order_id) REFERENCES shopping_cart_info(cart_id),
    FOREIGN KEY (shipper_id) REFERENCES shipper(shipper_id)
);

CREATE INDEX product_name ON product(product_name);
CREATE INDEX description ON product(description);

INSERT INTO user (username, password, role) VALUES ('admin', 'admin', 'admin');
