SELECT 
	status,
	COUNT(*) AS number_of_flights,
	MIN(scheduled_departure) AS earliest_scheduled_departure,
	MAX(scheduled_departure) AS latest_scheduled_departure
FROM flights
GROUP BY status
ORDER BY earliest_scheduled_departure;
