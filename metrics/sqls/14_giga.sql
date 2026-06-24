SELECT 
	airplane_code, 
	COUNT(*) 
FROM routes
GROUP BY airplane_code;
