DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS shopping_cart;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS shipping;

CREATE TABLE user (
  username TEXT PRIMARY KEY,
  password TEXT NOT NULL
);

CREATE TABLE post (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  title TEXT NOT NULL,
  body TEXT NOT NULL,
  FOREIGN KEY (author_id) REFERENCES user (username)
);

CREATE TABLE products (
    product_name TEXT PRIMARY KEY,
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
    cart_id TEXT PRIMARY KEY,
    quantity INTEGER,
    username TEXT,
    product_name TEXT,
    created_at TIMESTAMP,
    FOREIGN KEY (username) REFERENCES user(username)
    FOREIGN KEY (product_name) REFERENCES products(product_name)
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
    shipping_id TEXT PRIMARY KEY,
    address TEXT,
    date_shipped TIMESTAMP,
    order_id TEXT,
    cart_id TEXT,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
    FOREIGN KEY (cart_id) REFERENCES orders(cart_id)
);
