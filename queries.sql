-- SELECT pbc.product_id, p.product_name, pbc.quantity, sci.username, sci.created_at, sci.updated_at, SUM((p.price - p.discount) * pbc.quantity) AS product_total_price
-- FROM product_by_cart AS pbc
-- JOIN product AS p
-- ON pbc.product_id = p.product_id
-- JOIN shopping_cart_info AS sci
-- ON sci.cart_id = pbc.cart_id
-- WHERE pbc.cart_id = 'a59a9625-a108-4c0d-b180-00b5d28798ba'
-- GROUP BY pbc.product_id
-- ORDER BY sci.created_at ASC;


-- SELECT p.product_id, p.product_name, p.in_stock, pbc.quantity FROM product AS p
-- JOIN product_by_cart AS pbc
-- ON p.product_id = pbc.product_id
-- WHERE pbc.cart_id = 'a59a9625-a108-4c0d-b180-00b5d28798ba';


SELECT * FROM order_info AS oi
JOIN product_by_cart AS pbc
ON oi.order_id = pbc.cart_id
JOIN shopping_cart_info AS sci
ON pbc.cart_id = sci.cart_id
JOIN product AS p
ON p.product_id = pbc.product_id
WHERE sci.username = 'tanvir';
