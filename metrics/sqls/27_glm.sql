SELECT 
	airport_code, 
	airport_name, 
	city, 
	country, 
	coordinates
FROM airports
WHERE coordinates[1] < 0;
