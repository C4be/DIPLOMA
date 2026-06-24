SELECT 
	fare_conditions, 
	round(avg(price), 2) AS avg_price 
FROM bookings.segments 
GROUP BY fare_conditions;
