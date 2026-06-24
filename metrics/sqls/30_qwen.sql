SELECT 
	s.fare_conditions,
	COUNT(*) AS tickets_sold,
	AVG(s.price) AS avg_price,
	MIN(s.price) AS min_price,
	MAX(s.price) AS max_price
FROM tickets t
JOIN segments s ON t.ticket_no = s.ticket_no
GROUP BY s.fare_conditions;
