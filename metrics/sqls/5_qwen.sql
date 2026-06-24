SELECT fare_conditions, COUNT(*) AS seat_count
FROM seats
GROUP BY fare_conditions;
