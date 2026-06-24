SELECT 
    a.airport_code,
    a.airport_name,
    a.city,
    COUNT(f.flight_id) AS departures_count
FROM airports a
JOIN routes r ON r.departure_airport = a.airport_code
JOIN flights f ON f.route_no = r.route_no
WHERE r.validity @> bookings.now()
GROUP BY a.airport_code, a.airport_name, a.city
ORDER BY departures_count DESC
LIMIT 10;
