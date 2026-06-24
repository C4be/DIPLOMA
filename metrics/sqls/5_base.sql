
select fare_conditions, count(*) as seats_count
from seats
group by fare_conditions;
