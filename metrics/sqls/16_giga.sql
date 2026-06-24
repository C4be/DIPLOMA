SELECT *
FROM bookings
WHERE book_date::date >= '2025-12-01'::date
AND total_amount < 5000 
ORDER BY book_date;
