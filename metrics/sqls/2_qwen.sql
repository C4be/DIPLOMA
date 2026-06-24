SELECT
	airplane_code,
	model ->> lang() AS model_ru,
	range,
	speed
FROM airplanes_data;