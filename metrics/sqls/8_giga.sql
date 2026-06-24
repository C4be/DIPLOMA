SELECT 
	fare_conditions, 
	ROUND(AVG(price::NUMERIC), 2) AS avg_price 
FROM segments 
GROUP BY fare_conditions;
