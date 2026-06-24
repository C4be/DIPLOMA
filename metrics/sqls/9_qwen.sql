SELECT 
	s.ticket_no,
	s.flight_id,
	s.fare_conditions,
	s.price AS amount,
	ROUND((s.price - avg_by_class.avg_price) * 100.0 / avg_by_class.avg_price, 2) AS price_diff_percent
FROM bookings.segments s
JOIN (
	SELECT 
	fare_conditions,
	AVG(price) AS avg_price
	FROM bookings.segments
	GROUP BY fare_conditions
) avg_by_class ON s.fare_conditions = avg_by_class.fare_conditions
WHERE s.price > avg_by_class.avg_price
ORDER BY s.fare_conditions, s.price DESC, s.flight_id
LIMIT 100;
