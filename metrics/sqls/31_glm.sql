SELECT
	a.airport_code,
	a.city,
    COUNT(f.flight_id) AS departure_count
FROM airports_data a
JOIN routes r ON a.airport_code = r.departure_airport
JOIN flights f ON r.route_no = f.route_no
GROUP BY a.airport_code, a.city
ORDER BY departure_count DESC
LIMIT 10;
