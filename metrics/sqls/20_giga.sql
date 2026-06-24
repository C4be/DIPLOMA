SELECT 
	flight_id, 
	COUNT(*) AS flight_count
FROM flights
GROUP BY flight_id;
