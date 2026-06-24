
select
	s.ticket_no,
	s.flight_id,
	s.fare_conditions,
	s.price,
	round(100.0 * (s.price - avg_by_fare.avg_price) / avg_by_fare.avg_price, 2) as price_diff_percent
from segments s
join (
	select fare_conditions, avg(price) as avg_price
	from segments
	group by fare_conditions
) avg_by_fare on s.fare_conditions = avg_by_fare.fare_conditions
where s.price > avg_by_fare.avg_price
order by price_diff_percent desc
limit 100;
