SELECT 
	r.airplane_code,
	AVG(EXTRACT(EPOCH FROM (f.actual_arrival - f.actual_departure)) / 60.0) AS avg_duration
FROM flights f
JOIN routes r ON f.route_no = r.route_no
WHERE f.actual_departure IS NOT NULL 
AND f.actual_arrival IS NOT NULL
GROUP BY r.airplane_code
HAVING AVG(EXTRACT(EPOCH FROM (f.actual_arrival - f.actual_departure)) / 60.0) > 120
ORDER BY avg_duration DESC;
