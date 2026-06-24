
select
	r.airplane_code,
	avg(r.duration) as avg_duration
from routes r
group by r.airplane_code
having avg(r.duration) > interval '2 hours'
order by avg_duration desc;
