SELECT 
	flight_id, 
	status
FROM bookings.flights
WHERE status = 'Cancelled';
