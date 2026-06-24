SELECT
	f.flight_id,
	f.route_no,
	dep.city AS departure_city,
	dep.airport_name AS departure_airport,
	arr.city AS arrival_city,
	arr.airport_name AS arrival_airport
FROM tickets t
JOIN segments s ON s.ticket_no = t.ticket_no
JOIN flights f ON f.flight_id = s.flight_id
JOIN routes r ON r.route_no = f.route_no AND r.validity @> f.scheduled_departure
JOIN airports dep ON dep.airport_code = r.departure_airport
JOIN airports arr ON arr.airport_code = r.arrival_airport
WHERE t.ticket_no = '0005433348362'
ORDER BY f.scheduled_departure;
