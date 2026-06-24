SELECT
	airplane_code,
	COUNT(*) AS total_seats,
	SUM(CASE WHEN fare_conditions = 'Business' THEN 1 ELSE 0 END) AS business_seats,
	ROUND(100.0 * SUM(CASE WHEN fare_conditions = 'Business' THEN 1 ELSE 0 END) / COUNT(*), 2) AS business_percentage
FROM bookings.seats
GROUP BY airplane_code;
