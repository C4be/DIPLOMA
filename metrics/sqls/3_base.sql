
select
	airplane_code,
	range::numeric / speed as long_time
from airplanes_data
order by long_time desc;
