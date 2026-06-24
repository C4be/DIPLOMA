SELECT 
COUNT(*) AS airports_count,
CASE 
	WHEN airports_data.country IS NOT NULL THEN airports_data.country->>'name' 
	ELSE 'Unknown' 
END AS country
FROM routes
JOIN airports_data ON routes.departure_airport = airports_data.airport_code
GROUP BY 
	CASE 
		WHEN airports_data.country IS NOT NULL THEN airports_data.country->>'name' 
		ELSE 'Unknown' 
	END
ORDER BY 
airports_count DESC
LIMIT 5;
