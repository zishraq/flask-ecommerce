DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS shopping_cart;
DROP TABLE IF EXISTS orders;
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
    description TEXT NOT NULL,
    product_category TEXT NOT NULL,
    price FLOAT,
    discount FLOAT ,
    created_at TIMESTAMP,
    created_by TEXT,
    updated_at TIMESTAMP,
    updated_by TEXT,
    in_stock INTEGER,
    total_sold INTEGER
);

CREATE TABLE shopping_cart (
    cart_id TEXT,
    product_id TEXT,
    quantity INTEGER,
    username TEXT,
    created_at TIMESTAMP,
    PRIMARY KEY(cart_id, product_id),
    FOREIGN KEY (username) REFERENCES user(username),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

CREATE TABLE orders (
    order_id TEXT,
    cart_id TEXT,
    date_created TIMESTAMP,
    order_final INTEGER,
    PRIMARY KEY(order_id, cart_id),
    FOREIGN KEY (cart_id) REFERENCES shopping_cart(cart_id)
);

CREATE TABLE shipping (
    shipping_id TEXT,
    order_id TEXT,
    address TEXT,
    date_shipped TIMESTAMP,
    PRIMARY KEY(shipping_id, order_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
