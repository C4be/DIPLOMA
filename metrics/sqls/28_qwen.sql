SELECT
	status,
	COUNT(*) AS count,
	MIN(scheduled_departure) AT TIME ZONE 'Europe/Moscow' AS min_scheduled_departure,
	MAX(scheduled_departure) AT TIME ZONE 'Europe/Moscow' AS max_scheduled_departure
FROM flights
GROUP BY status
ORDER BY min_scheduled_departure;
