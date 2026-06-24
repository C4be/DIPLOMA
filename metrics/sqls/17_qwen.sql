SELECT 
	book_date::date AS booking_date, 
	SUM(total_amount) AS total_sum
FROM bookings
GROUP BY book_date::date
ORDER BY booking_date;
