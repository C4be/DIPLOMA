
select
	book_ref, count(*) as booking_count
from tickets
where substr(passenger_name, 1, 1) = 'Ž'
group by book_ref;
