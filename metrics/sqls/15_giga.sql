SELECT 
	airplane_code, 
	AVG(EXTRACT(EPOCH FROM scheduled_arrival - scheduled_departure))::numeric / 3600 AS avg_duration
FROM flights
JOIN routes ON flights.route_no = routes.route_no
WHERE EXTRACT(EPOCH FROM scheduled_arrival - scheduled_departure) / 3600 > 2
GROUP BY airplane_code;
