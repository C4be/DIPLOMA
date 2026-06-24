SELECT 
	book_date, 
	SUM(total_amount) AS total_sum
FROM bookings
WHERE total_amount > 10000
GROUP BY book_date
ORDER BY total_sum DESC;
