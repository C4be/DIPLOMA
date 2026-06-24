SELECT 
	airplane_code, 
	COUNT(*) AS route_count
FROM routes
GROUP BY airplane_code;
