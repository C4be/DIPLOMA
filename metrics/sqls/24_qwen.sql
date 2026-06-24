SELECT 
	country, 
	COUNT(*) AS airports_count
FROM airports
GROUP BY country
ORDER BY airports_count DESC;
