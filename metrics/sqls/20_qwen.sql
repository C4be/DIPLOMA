SELECT 
	route_no, 
	COUNT(*) AS flights_count
FROM flights
GROUP BY route_no;
