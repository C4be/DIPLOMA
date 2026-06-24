SELECT airport_code, airport_name, city, country, coordinates, timezone
FROM airports
WHERE country = 'Russia' OR country = 'Россия';
