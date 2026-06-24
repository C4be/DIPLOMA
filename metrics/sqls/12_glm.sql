SELECT 
	t.passenger_name, 
	COUNT(t.ticket_no) AS ticket_count
FROM tickets t
GROUP BY t.passenger_name
ORDER BY ticket_count DESC;
