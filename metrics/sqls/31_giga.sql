WITH departures_count AS (
	SELECT 
		a.airport_code,
		COUNT(f.flight_id) AS departures_count
	FROM airports_data a
	JOIN routes r ON a.airport_code = r.departure_airport
	JOIN flights f ON r.route_no = f.route_no
	GROUP BY a.airport_code
)
SELECT 
	airport_code, 
	departures_count
FROM departures_count
ORDER BY departures_count DESC
LIMIT 10;
