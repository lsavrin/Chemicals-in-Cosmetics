USE cosmetic_chemicals;

--drop trigger stock_management_trigger
--drop table transaction_lineitem
--drop table transactions
--drop table stock_movement_log 
--drop table product_in_store
--drop table saleschannel
--drop table store
--drop table customer
--drop table gender
--drop table product_chemical
--drop table chemical
--drop table products
--drop table product_name
--drop table color_shade_formulation
--drop table subcategory
--drop table category
--drop table brand
--drop table company

CREATE TABLE company (
    company_id INT IDENTITY(1,1) PRIMARY KEY,
    company_name VARCHAR(255),
    company_id_number VARCHAR(50)
);

CREATE TABLE brand (
    brand_id INT IDENTITY(1,1) PRIMARY KEY,
    brand_name VARCHAR(255),
    company_id INT FOREIGN KEY REFERENCES company(company_id)
);

CREATE TABLE category (
    category_id INT IDENTITY(1,1) PRIMARY KEY,
    category_name VARCHAR(255),
    category_id_number VARCHAR(50)
);

CREATE TABLE subcategory (
    subcategory_id INT IDENTITY(1,1) PRIMARY KEY,
    sub_cat_name VARCHAR(255),
    subcategory_id_number VARCHAR(50),
    category_id INT FOREIGN KEY REFERENCES category(category_id)
);

CREATE TABLE color_shade_formulation (
    csf_id INT IDENTITY(1,1) PRIMARY KEY,
    csf_name VARCHAR(255),
    csf_id_number VARCHAR(50)
);

CREATE TABLE product_name(
	product_name_id INT IDENTITY(1,1) PRIMARY KEY,
	product_name VARCHAR(255)
	);

CREATE TABLE products (
    product_id INT IDENTITY(1,1) PRIMARY KEY,
    product_name_id INT FOREIGN KEY REFERENCES product_name(product_name_id),
    brand_id INT FOREIGN KEY REFERENCES brand(brand_id),
    subcategory_id INT FOREIGN KEY REFERENCES subcategory(subcategory_id),
    csf_id INT NULL FOREIGN KEY REFERENCES color_shade_formulation(csf_id),
    CDPHID VARCHAR(50)
);

CREATE TABLE chemical (
    chemical_id INT IDENTITY(1,1) PRIMARY KEY,
    chemical_name VARCHAR(255)
);

CREATE TABLE product_chemical (
    chemical_id INT,
    product_id INT,
    initial_date_reported DATE,
    most_recent_date_reported DATE,
    discontinued_date DATE,
    chemical_created_at DATE,
    chemical_updated_at DATE,
    chemical_date_removed DATE,
    chemical_id_number VARCHAR(50),
    PRIMARY KEY (chemical_id, product_id),
    FOREIGN KEY (chemical_id) REFERENCES chemical(chemical_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);


CREATE TABLE gender (
    gender_id INT PRIMARY KEY,
    gender VARCHAR(50)
);

CREATE TABLE store_type (
	store_type_id INT PRIMARY KEY,
	store_type VARCHAR(255)
);

CREATE TABLE saleschannel (
    channel_id INT PRIMARY KEY,
    channel_name VARCHAR(255)
);

CREATE TABLE store (
    store_id INT PRIMARY KEY,
    store_name VARCHAR(255),
	store_type_id INT FOREIGN KEY REFERENCES store_type(store_type_id)
);

CREATE TABLE customer (
    customer_id INT IDENTITY(1,1) PRIMARY KEY,
    customer_name VARCHAR(255),
    gender_id INT FOREIGN KEY REFERENCES gender(gender_id)
);

CREATE TABLE product_in_store (
    product_store_id INT IDENTITY(1,1) PRIMARY KEY,
    store_id INT FOREIGN KEY REFERENCES store(store_id),
    product_id INT FOREIGN KEY REFERENCES products(product_id),
    price DECIMAL(10,2),
    stock_remaining INT,
    CONSTRAINT uq_product_store UNIQUE (store_id, product_id)
);

CREATE TABLE stock_movement_log (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    product_store_id INT FOREIGN KEY REFERENCES product_in_store(product_store_id),
    change_date DATETIME DEFAULT GETDATE(),
    quantity_changed INT,
    new_stock_remaining INT,
    reason VARCHAR(50),
    related_transaction_id INT NULL
);

CREATE TABLE transactions (
    transaction_id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_date DATE,
    transaction_total DECIMAL(10,2),
	transaction_id_number INT,
    customer_id INT FOREIGN KEY REFERENCES customer(customer_id),
	channel_id INT FOREIGN KEY REFERENCES saleschannel(channel_id)
);

CREATE TABLE transaction_lineitem (
    lineitem_id INT IDENTITY(1,1) PRIMARY KEY,
    transaction_id INT FOREIGN KEY REFERENCES transactions(transaction_id),
    product_store_id INT FOREIGN KEY REFERENCES product_in_store(product_store_id),
    sale_quantity INT,
    line_total DECIMAL(10,2),
	unit_price DECIMAL(10,2)
);


CREATE TRIGGER stock_management_trigger
ON transaction_lineitem
INSTEAD OF INSERT
AS
BEGIN
    SET NOCOUNT ON;
    IF EXISTS (
        SELECT 1
        FROM inserted
        JOIN product_in_store ON inserted.product_store_id = product_in_store.product_store_id
        WHERE product_in_store.stock_remaining < inserted.sale_quantity
    )
    BEGIN
        RAISERROR ('Not enough stock remaining to complete sale.', 16, 1);
        ROLLBACK TRANSACTION;
        RETURN;
    END

    INSERT INTO transaction_lineitem (transaction_id, product_store_id, sale_quantity, line_total, unit_price)
    SELECT transaction_id, product_store_id, sale_quantity, line_total, unit_price
    FROM inserted;

    UPDATE product_in_store
    SET product_in_store.stock_remaining = product_in_store.stock_remaining - inserted.sale_quantity
    FROM product_in_store 
    JOIN inserted ON product_in_store.product_store_id = inserted.product_store_id;

    INSERT INTO stock_movement_log (product_store_id, quantity_changed, new_stock_remaining, reason, related_transaction_id)
    SELECT 
        inserted.product_store_id,
        -inserted.sale_quantity,
        product_in_store.stock_remaining,
        'sale',
        inserted.transaction_id
    FROM inserted
    JOIN product_in_store ON product_in_store.product_store_id = inserted.product_store_id;
END;

--select * from transaction_lineitem
--select * from stock_movement_log

--INSERT INTO transaction_lineitem (transaction_id, product_store_id, sale_quantity, line_total, unit_price)
--VALUES (3500, 361, 2, 60.48, 30.24)

INSERT INTO gender (gender_id, gender) VALUES
(1, 'female'),
(2, 'male'),
(3, 'non-binary');

INSERT INTO saleschannel (channel_id, channel_name) VALUES
(1, 'online'),
(2, 'in-store');

INSERT INTO store_type(store_type_id,store_type) VALUES
(1, 'mass market'),
(2, 'drugstore'),
(3, 'big box'),
(4, 'specialized')

INSERT INTO store (store_id, store_name, store_type_id) VALUES
(1, 'macys', 3),
(2, 'cvs', 2),
(3, 'sephora', 4),
(4, 'ulta', 4),
(5, 'amazon', 1),
(6, 'nordstrom', 3),
(7, 'target', 1),
(8, 'walmart', 1),
(9, 'walgreens', 2);






