
select
	passenger_name,
	count(*) as tickets_count
from tickets t
group by passenger_id, passenger_name
having count(1) = 100
order by tickets_count desc;
