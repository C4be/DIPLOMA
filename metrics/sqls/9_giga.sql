WITH avg_price AS (
	SELECT fare_conditions, AVG(price) as avg_price
	FROM segments
	GROUP BY fare_conditions
)
SELECT 
	t.ticket_no,
	s.price,
	((s.price - avg_price.avg_price)/avg_price.avg_price)*100 AS percent_deviation
FROM segments s
JOIN tickets t ON s.ticket_no = t.ticket_no
JOIN avg_price ON s.fare_conditions = avg_price.fare_conditions
WHERE s.price > avg_price.avg_price
ORDER BY percent_deviation DESC
LIMIT 100;
