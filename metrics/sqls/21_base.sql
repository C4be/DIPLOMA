
select
	flight_id,
	actual_arrival - scheduled_arrival as delay_time
from flights
where status = 'Arrived'
and actual_arrival - scheduled_arrival > interval '10 minutes'
order by delay_time desc;
