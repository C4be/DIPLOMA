SELECT 
	date_trunc('day', book_date) AS booking_day, 
	SUM(total_amount) AS total_bookings
FROM bookings
GROUP BY date_trunc('day', book_date);
