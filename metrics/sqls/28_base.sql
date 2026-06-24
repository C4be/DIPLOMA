SELECT
    status,
    count(*) AS count,
    min(scheduled_departure) AS min_scheduled_departure,
    max(scheduled_departure) AS max_scheduled_departure
FROM flights
GROUP BY status
ORDER BY min_scheduled_departure;
