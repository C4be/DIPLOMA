
select
	airport_code,
	airport_name,
	country,
	coordinates[1] AS latitude,
	coordinates[0] AS longitude
from airports
where coordinates[1] < 0;
