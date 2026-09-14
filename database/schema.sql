CREATE DATABASE smart_expense_tracker;

USE smart_expense_tracker;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL
);

CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    type ENUM('Income', 'Expense') NOT NULL,
    description VARCHAR(255),
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,

    FOREIGN KEY (category_id)
        REFERENCES categories(id)
        ON DELETE RESTRICT
);

INSERT INTO categories (name, type) VALUES
('Salary', 'Income'),
('Freelance', 'Income'),
('Other Income', 'Income'),
('Food', 'Expense'),
('Transport', 'Expense'),
('Shopping', 'Expense'),
('Bills', 'Expense'),
('Entertainment', 'Expense'),
('Healthcare', 'Expense'),
('Education', 'Expense'),
('Other Expense', 'Expense');