SELECT 
	flight_id, 
	(actual_arrival - scheduled_arrival) AS delay_time
FROM flights
WHERE (actual_arrival - scheduled_arrival) > interval '10 minutes';
