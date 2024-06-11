import streamlit as st
import pandas as pd
import numpy as np
import datetime
from joblib import load
from sklearn.ensemble import RandomForestRegressor
import json
import requests
import matplotlib.pyplot as plt

# Load your model
model = load('new.joblib')

# Initialize a dataframe to store sensor data
data = pd.DataFrame(columns=['timestamp', 'temp', 'humidity', 'soil_moisture', 'prediction'])

# Blynk configuration
BLYNK_AUTH_TOKEN = "osKAfPJ15zi-PIdeGskhreifuXXnBTWi"
BLYNK_API_URL = f"http://blynk-cloud.com/{BLYNK_AUTH_TOKEN}/get"

# Define a function to fetch data from Blynk
def fetch_blynk_data():
    temp_url = f"{BLYNK_API_URL}/V2"
    humidity_url = f"{BLYNK_API_URL}/V3"
    soil_moisture_url = f"{BLYNK_API_URL}/V1"
    
    temp_response = requests.get(temp_url)
    humidity_response = requests.get(humidity_url)
    soil_moisture_response = requests.get(soil_moisture_url)
    
    if temp_response.status_code == 200 and humidity_response.status_code == 200 and soil_moisture_response.status_code == 200:
        temp = float(temp_response.json()[0])
        humidity = float(humidity_response.json()[0])
        soil_moisture = float(soil_moisture_response.json()[0])
        return temp, humidity, soil_moisture
    else:
        st.error("Failed to fetch data from Blynk")
        return None, None, None

# Define a function to predict irrigation timing
def predict_irrigation(temp, humidity, soil_moisture):
    features = np.array([[temp, humidity, soil_moisture]])
    prediction = model.predict(features)
    return prediction[0]

# Function to add new data
def add_new_data(temp, humidity, soil_moisture, prediction):
    global data
    new_data = {
        'timestamp': datetime.datetime.now(),
        'temp': temp,
        'humidity': humidity,
        'soil_moisture': soil_moisture,
        'prediction': prediction
    }
    data = data.append(new_data, ignore_index=True)

# Streamlit App
st.title("Smart Irrigation Prediction")

# Fetch data from Blynk
temp, humidity, soil_moisture = fetch_blynk_data()

# If data is successfully fetched, make a prediction and add it to the dataframe
if temp is not None and humidity is not None and soil_moisture is not None:
    prediction = predict_irrigation(temp, humidity, soil_moisture)
    add_new_data(temp, humidity, soil_moisture, prediction)
    st.write(f"Latest Data: Temperature: {temp} °C, Humidity: {humidity} %, Soil Moisture: {soil_moisture} %")
    st.write(f"Prediction: {prediction} %")

# Display the data in tabular form
st.subheader("Sensor Data")
st.dataframe(data)

# Plot time series graphs for fluctuations
st.subheader("Sensor Data Fluctuations")

if not data.empty:
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data.set_index('timestamp', inplace=True)
    
    resampled_data = data.resample('15S').mean()

    fig, ax = plt.subplots(3, 1, figsize=(10, 15))
    
    ax[0].plot(resampled_data.index, resampled_data['temp'], label='Temperature (°C)')
    ax[0].set_title('Temperature Fluctuations')
    ax[0].set_xlabel('Time')
    ax[0].set_ylabel('Temperature (°C)')
    ax[0].legend()

    ax[1].plot(resampled_data.index, resampled_data['humidity'], label='Humidity (%)', color='orange')
    ax[1].set_title('Humidity Fluctuations')
    ax[1].set_xlabel('Time')
    ax[1].set_ylabel('Humidity (%)')
    ax[1].legend()

    ax[2].plot(resampled_data.index, resampled_data['soil_moisture'], label='Soil Moisture (%)', color='green')
    ax[2].set_title('Soil Moisture Fluctuations')
    ax[2].set_xlabel('Time')
    ax[2].set_ylabel('Soil Moisture (%)')
    ax[2].legend()

    st.pyplot(fig)
else:
    st.write("No data to display yet.")
