SELECT r.route_no,
    dep.airport_code dep_airport, dep.country dep_country, dep.city dep_city,
    arr.airport_code arr_airport, arr.country arr_country, arr.city arr_city
FROM segments s
    JOIN flights f ON f.flight_id = s.flight_id
    JOIN routes r ON r.route_no = f.route_no AND r.validity @> f.scheduled_departure
    JOIN airports dep ON dep.airport_code = r.departure_airport
    JOIN airports arr ON arr.airport_code = r.arrival_airport
WHERE s.ticket_no = '0005433348362'
ORDER BY f.scheduled_departure;
