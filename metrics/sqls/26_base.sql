
select
	country,
	count(*) as airports_count
from airports
group by country
HAVING COUNT(*) <= 5
ORDER BY airports_count DESC;
