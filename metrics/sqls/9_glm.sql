SELECT 
	ticket_no, 
	flight_id, 
	fare_conditions, 
	price AS amount,
	AVG(price) OVER (PARTITION BY fare_conditions) AS avg_fare_amount,
	(price - AVG(price) OVER (PARTITION BY fare_conditions)) * 100.0 / 
	AVG(price) OVER (PARTITION BY fare_conditions) AS deviation_percent
FROM segments
LIMIT 100;
