SELECT
	flight_id,
	actual_arrival - scheduled_arrival AS delay_time
FROM flights
WHERE actual_arrival - scheduled_arrival > INTERVAL '10 minutes';
