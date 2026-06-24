SELECT 
	airplane_code, 
	model::jsonb->'model_ru' AS model_ru, 
	range, 
	speed 
FROM airplanes_data;