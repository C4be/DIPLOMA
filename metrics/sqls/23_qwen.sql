SELECT DISTINCT 
	(city ->> 'en') AS city, 
	airport_code, 
	(airport_name ->> 'en') AS airport_name
FROM airports_data
WHERE (country ->> 'en') = 'Iran';
