SELECT 
	fare_conditions,
	COUNT(*) AS tickets_sold,
	AVG(price) AS avg_price,
	MIN(price) AS min_price,
	MAX(price) AS max_price
FROM segments
GROUP BY fare_conditions;
