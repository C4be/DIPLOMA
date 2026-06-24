
select *
from bookings
where total_amount = 2500 
 and book_date::date  between '2025-09-01'::date and '2025-09-02'::date
order by book_date;
