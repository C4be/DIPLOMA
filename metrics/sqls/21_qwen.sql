SELECT 
	flight_id,
	EXTRACT(EPOCH FROM (actual_departure - scheduled_departure)) / 60 AS delay_time
FROM flights
WHERE actual_departure IS NOT NULL 
	AND scheduled_departure IS NOT NULL 
	AND status IN ('Departed', 'Arrived')
	AND EXTRACT(EPOCH FROM (actual_departure - scheduled_departure)) / 60 > 10
ORDER BY delay_time DESC;
