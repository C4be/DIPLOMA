
select
	fare_conditions,
	round(avg(price), 2) as avg_price
from segments
group by fare_conditions;
