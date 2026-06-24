
select
	airplane_code,
	count(*) as routes_count
from routes
group by airplane_code;
