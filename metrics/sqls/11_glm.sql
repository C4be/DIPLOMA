SELECT 
	book_ref, COUNT(*) AS booking_count
FROM tickets
WHERE passenger_name LIKE 'Ž%'
GROUP BY book_ref;
