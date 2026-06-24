SELECT
	a.airport_code,
	a.city,
	a.airport_name,
	COUNT(f.flight_id) AS departures_count
FROM airports a
JOIN routes r ON a.airport_code = r.departure_airport
JOIN flights f ON r.route_no = f.route_no
GROUP BY a.airport_code, a.city, a.airport_name
ORDER BY departures_count DESC
LIMIT 10;
