WITH airport_count AS (
	SELECT country, COUNT(*) as airport_count
	FROM airports_data
	GROUP BY country
)
SELECT country, airport_count
FROM airport_count
ORDER BY airport_count DESC;
