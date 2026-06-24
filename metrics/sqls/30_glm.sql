SELECT 
    s.fare_conditions,
    COUNT(*) AS tickets_sold,
    ROUND(AVG(s.price), 2) AS avg_price,
    MIN(s.price) AS min_price,
    MAX(s.price) AS max_price
FROM segments s
GROUP BY s.fare_conditions;
