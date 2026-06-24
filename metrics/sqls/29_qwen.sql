SELECT DISTINCT
	r.route_no,
	da.airport_name->>'en' AS departure_airport,
	aa.airport_name->>'en' AS arrival_airport,
	da.country->>'en' AS departure_country,
	da.city->>'en' AS departure_city,
	aa.country->>'en' AS arrival_country,
	aa.city->>'en' AS arrival_city
FROM tickets t
JOIN segments s ON t.ticket_no = s.ticket_no
JOIN flights f ON s.flight_id = f.flight_id
JOIN routes r ON f.route_no = r.route_no
JOIN airports_data da ON r.departure_airport = da.airport_code
JOIN airports_data aa ON r.arrival_airport = aa.airport_code
WHERE t.ticket_no = '0005433348362';
