use cosmetic_chemicals;

SET STATISTICS TIME ON
SET STATISTICS IO ON

CREATE INDEX idx_product_lineitem ON transaction_lineitem(product_store_id) 
CREATE INDEX idx_transaction_lineitem ON transaction_lineitem(transaction_id)
CREATE INDEX idx_product_store ON product_in_store(product_id)
CREATE INDEX idx_product_subcat ON products(subcategory_id)

--- query breakdowns: purely tables ---

---# of products for each chemical---
SELECT
chemical.chemical_name,
count(*) as total_count
FROM chemical
JOIN product_chemical ON product_chemical.chemical_id = chemical.chemical_id
GROUP BY chemical.chemical_name
ORDER BY total_count DESC

--counts are different but this is more accurate. removes duplication of the same chemicals under different "ID"

---Average transactions size by store type---
WITH Transaction_Total AS(
SELECT 
transactions.transaction_id,
MAX(store_type.store_type) as type, --max needed to avoid having to include in the group by
MAX(transactions.transaction_total) as true_total
FROM store_type
JOIN store on store.store_type_id = store_type.store_type_id
JOIN product_in_store on product_in_store.store_id = store.store_id
JOIN transaction_lineitem on product_in_store.product_store_id = transaction_lineitem.product_store_id
JOIN transactions on transactions.transaction_id = transaction_lineitem.transaction_id
GROUP BY transactions.transaction_id
) --view helps us to look at the total on a transaction basis and avoid duplication of the transaction total so we get accurate averages

SELECT 
Transaction_Total.type,
SUM(Transaction_Total.true_total) as total_spend,
COUNT(Transaction_Total.true_total) as total_transaction_count,
ROUND(AVG(Transaction_Total.true_total),2) as average_total_spend
FROM Transaction_Total
GROUP BY Transaction_Total.type
ORDER BY average_total_spend DESC


---Categories by transaction rate---

--Original Query
SELECT
category.category_name,
SUM(transaction_lineitem.line_total) as total_spend,
ROUND(AVG(transaction_lineitem.line_total),2) as average_total_spend
FROM category
JOIN subcategory ON category.category_id = subcategory.category_id
JOIN products ON products.subcategory_id = subcategory.subcategory_id
JOIN product_in_store on product_in_store.product_id = products.product_id
JOIN transaction_lineitem on product_in_store.product_store_id = transaction_lineitem.product_store_id
GROUP BY category.category_name
ORDER BY average_total_spend DESC

--Attempt 1: wrong outcome
WITH ProductAverage AS(
SELECT
products.product_id,
products.subcategory_id,
ROUND(AVG(transaction_lineitem.line_total),2) as average_total_spend
FROM transaction_lineitem
JOIN product_in_store ON product_in_store.product_store_id = transaction_lineitem.product_store_id
JOIN products ON products.product_id = product_in_store.product_id
GROUP BY products.product_id, products.subcategory_id
)

SELECT
category.category_name,
ROUND(AVG(average_total_spend),2) as category_average
FROM ProductAverage
JOIN subcategory on subcategory.subcategory_id = ProductAverage.subcategory_id
JOIN category on category.category_id = subcategory.category_id
GROUP BY category.category_name
ORDER BY category_average DESC


-- Attempt 2: Works correctly
WITH ProductDetails AS(
SELECT
products.product_id,
products.subcategory_id,
COUNT(transaction_lineitem.line_total) as transaction_volume,
SUM(transaction_lineitem.line_total) as product_total_spend
FROM transaction_lineitem
JOIN product_in_store ON product_in_store.product_store_id = transaction_lineitem.product_store_id
JOIN products ON products.product_id = product_in_store.product_id
GROUP BY products.product_id, products.subcategory_id
),
CategoryAverage AS(
SELECT
subcategory.category_id,
SUM(transaction_volume) AS total_volume,
SUM(product_total_spend) AS cat_total_spend
FROM ProductDetails
JOIN subcategory on subcategory.subcategory_id = ProductDetails.subcategory_id
GROUP BY subcategory.category_id
)
SELECT
category.category_name,
ROUND(CategoryAverage.cat_total_spend/CategoryAverage.total_volume,2) as category_average
FROM CategoryAverage
JOIN category on category.category_id = CategoryAverage.category_id
ORDER BY category_average DESC