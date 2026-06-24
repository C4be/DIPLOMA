SELECT 
	passenger_id,
	passenger_name,
	COUNT(*) AS ticket_count
FROM tickets
GROUP BY passenger_id, passenger_name
ORDER BY ticket_count DESC
LIMIT 10;
