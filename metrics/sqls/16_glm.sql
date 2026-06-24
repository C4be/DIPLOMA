SELECT book_ref, book_date, total_amount
FROM bookings
WHERE total_amount = 2500
AND book_date >= '2025-09-01'::timestamptz
AND book_date < '2025-09-03'::timestamptz
ORDER BY book_date;
