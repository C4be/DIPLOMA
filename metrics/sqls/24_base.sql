
select
	country,
	count(*) as airports_count
from airports
group by country
order by airports_count desc;
