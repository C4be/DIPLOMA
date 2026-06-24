SELECT 
	airplane_code, 
	model ->> 'ru' AS model_ru, 
	range, 
	speed 
FROM airplanes_data;