SELECT 
	country, 
	COUNT(*) AS airport_count
FROM airports
GROUP BY country
ORDER BY airport_count DESC
LIMIT 5;
