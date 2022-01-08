DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;
DROP TABLE IF EXISTS products;

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
  FOREIGN KEY (author_id) REFERENCES user (id)
);

CREATE TABLE products (
    product_name TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    product_category TEXT NOT NULL,
    price FLOAT,
    discount FLOAT ,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    in_stock INTEGER,
    total_sold INTEGER
);