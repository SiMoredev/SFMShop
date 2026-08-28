CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    quantity INTEGER DEFAULT 0
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    total DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

INSERT INTO users (name, email) VALUES 
    ('Sergey', 'sergey@test.ru'), 
    ('Anna', 'anna@test.ru'), 
    ('Anton', 'anton@test.ru');

INSERT INTO orders (user_id, total) VALUES 
    (1, 7500), 
    (2, 500);

INSERT INTO products (name, price, quantity) VALUES
    ('Pizza', 1500, 5), 
    ('Bread', 150, 10), 
    ('Cheese', 1500, 2), 
    ('Milk', 100, 3), 
    ('Chocolate', 100, 10);

INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
    (1, 2, 2, 1500),
    (1, 1, 3, 1500),
    (2, 5, 5, 100);