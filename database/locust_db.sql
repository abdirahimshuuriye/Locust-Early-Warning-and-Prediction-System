USE locust_prediction_db;

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT AUTO_INCREMENT PRIMARY KEY,
    region VARCHAR(100),
    country VARCHAR(100),
    start_year INT,
    start_month INT,
    ppt FLOAT,
    tmax FLOAT,
    soil_moisture FLOAT,
    prediction_result VARCHAR(20),
    risk_level VARCHAR(50),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);