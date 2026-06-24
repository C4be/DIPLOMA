SELECT 
	book_date::date AS booking_date,
	SUM(total_amount) AS total_sum
FROM bookings
GROUP BY book_date::date
HAVING SUM(total_amount) > 10000
ORDER BY total_sum DESC;
