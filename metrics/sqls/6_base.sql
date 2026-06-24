
select
	airplane_code,
	count(1) as total_seats,
	round(100.0 * count(1) filter (where fare_conditions = 'Business') / count(*), 2) as business_percent
from seats
group by airplane_code
order by business_percent desc;
