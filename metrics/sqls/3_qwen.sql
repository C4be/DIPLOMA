SELECT
	airplane_code,
	range::numeric / speed AS long_time
FROM airplanes_data
ORDER BY long_time ASC;
