SELECT
	airplane_code,
	AVG(scheduled_arrival - scheduled_departure) AS avg_duration
FROM bookings.timetable
GROUP BY airplane_code
HAVING AVG(scheduled_arrival - scheduled_departure) > INTERVAL '2 hours';
