SELECT 
	airplane_code,
	COUNT(*) AS total_seats,
	ROUND(COUNT(*) FILTER (WHERE fare_conditions = 'Business') * 100.0 / NULLIF(COUNT(*), 0), 2) AS business_percent
FROM seats
GROUP BY airplane_code
ORDER BY business_percent DESC;
