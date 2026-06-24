
select
	book_date::date as booking_date,
	sum(total_amount) as total_sum
from bookings
group by book_date::date
having sum(total_amount) > 10000
order by total_sum desc;
