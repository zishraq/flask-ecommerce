DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS shopping_cart;
DROP TABLE IF EXISTS products_by_cart;
DROP TABLE IF EXISTS shopping_cart_info;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_info;
DROP TABLE IF EXISTS carts_by_orders;
DROP TABLE IF EXISTS shipping;

CREATE TABLE user (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL,
  name TEXT,
  email TEXT,
  phone TEXT,
  role TEXT,
  joined_at TIMESTAMP
);

CREATE TABLE products (
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
    tag_id INT,
    tag_name TEXT,
    created_at TIMESTAMP,
    created_by TEXT ,
    updated_at TIMESTAMP,
    updated_by TEXT,
    PRIMARY KEY (tag_name),
    FOREIGN KEY (created_by) REFERENCES user(username),
    FOREIGN KEY (updated_by) REFERENCES user(username)
);

CREATE TABLE products_by_tags (
    tag_name TEXT,
    product_id TEXT,
    PRIMARY KEY (tag_name, product_id),
    FOREIGN KEY (tag_name) REFERENCES product_tags(tag_name),
    FOREIGN key (product_id) REFERENCES products(product_id)
);

CREATE TABLE shopping_cart_info (
    cart_id TEXT,
    username TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY(cart_id),
    FOREIGN KEY (username) REFERENCES user(username)
);

CREATE TABLE products_by_cart (
    cart_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    added_at TIMESTAMP,
    updated_at TIMESTAMP,
    PRIMARY KEY(cart_id, product_id),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart_info(cart_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE order_info (
    order_id TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    is_confirmed INTEGER,
    PRIMARY KEY(order_id)
);

CREATE TABLE carts_by_orders (
    order_id TEXT,
    cart_id TEXT,
    added_at TIMESTAMP,
    PRIMARY KEY(order_id, cart_id),
    FOREIGN KEY (order_id) REFERENCES order_info(order_id),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart_info(cart_id)
);

CREATE TABLE shipping (
    shipping_id TEXT,
    order_id TEXT,
    address TEXT,
    date_shipped TIMESTAMP,
    PRIMARY KEY(shipping_id, order_id),
    FOREIGN KEY (order_id) REFERENCES order_info(order_id)
);
