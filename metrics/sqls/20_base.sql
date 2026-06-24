
select
	route_no,
	count(*) as flights_count
from flights
group by route_no;
