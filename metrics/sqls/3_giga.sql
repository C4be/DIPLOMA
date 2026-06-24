WITH flight_segments AS (
	SELECT 
		flight_id,
		scheduled_departure,
		scheduled_arrival,
		EXTRACT(EPOCH FROM (scheduled_arrival - scheduled_departure))::float AS long_time
	FROM flights
)
SELECT flight_id, long_time
FROM flight_segments
ORDER BY long_time DESC;
