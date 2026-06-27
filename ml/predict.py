import pandas as pd
import joblib

# Load saved model and target encoder
model = joblib.load("models/saved_model.pkl")
target_encoder = joblib.load("models/target_encoder.pkl")

# Sample input data
sample_data = pd.DataFrame([{
    "REGION": "Bari",
    "COUNTRYNAME": "Somalia",
    "STARTYEAR": 2020,
    "STARTMONTH": 5,
    "PPT": 25.5,
    "TMAX": 34.2,
    "SOILMOISTURE": 12.8
}])

# Make prediction
prediction = model.predict(sample_data)
prediction_label = target_encoder.inverse_transform(prediction)

print("Prediction Result:", prediction_label[0])

if prediction_label[0].lower() == "yes":
    print("Warning: Locust outbreak risk detected.")
else:
    print("No locust outbreak risk detected.")