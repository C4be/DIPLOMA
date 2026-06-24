SELECT fare_conditions, SUM(price) AS total_revenue
FROM bookings.segments
GROUP BY fare_conditions;
