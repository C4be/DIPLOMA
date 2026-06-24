SELECT 
	airport_code,
	airport_name,
	country,
	coordinates[1] AS latitude,
	coordinates[0] AS longitude
FROM airports
WHERE coordinates[1] < 0;
