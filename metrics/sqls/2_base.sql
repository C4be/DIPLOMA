select
	airplane_code,
	model->>'ru' as model_ru,
	range,
	speed
from airplanes_data;