SELECT 
	country, 
	COUNT(*) AS airports_count
FROM airports
GROUP BY country
HAVING COUNT(*) <= 5
ORDER BY airports_count DESC;
