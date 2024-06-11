import streamlit as st
import pandas as pd
import numpy as np
import datetime
from joblib import load
from sklearn.ensemble import RandomForestRegressor
import json
import matplotlib.pyplot as plt

# Load your model
model = load('new.joblib')

# Initialize a dataframe to store sensor data
data = pd.DataFrame(columns=['timestamp', 'temp', 'humidity', 'soil_moisture', 'prediction'])

# Define a function to predict irrigation timing
def predict_irrigation(temp, humidity, soil_moisture):
    features = np.array([[temp, humidity, soil_moisture]])
    st.write("Features:", features)  # Log the features
    st.write("Features shape:", features.shape)  # Log the shape of features
    try:
        prediction = model.predict(features)
        return prediction[0]
    except ValueError as e:
        st.error(f"ValueError: {e}")
        return None

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

# Function to handle POST requests
def handle_post_request(request):
    request_data = json.loads(request.body)
    temp = request_data['temp']
    humidity = request_data['humidity']
    soil_moisture = request_data['soil_moisture']
    
    # Make prediction
    prediction = predict_irrigation(temp, humidity, soil_moisture)
    
    # Store data in the dataframe
    if prediction is not None:
        add_new_data(temp, humidity, soil_moisture, prediction)
    
    response = {'prediction': prediction}
    return response

# Streamlit App
st.title("Smart Irrigation Prediction")

# Add random data to the dataframe
for _ in range(20):  # Adding 20 entries
    temp = np.random.uniform(20, 30)  # Random temperature between 20 and 30
    humidity = np.random.uniform(50, 70)  # Random humidity between 50 and 70
    soil_moisture = np.random.uniform(60, 80)  # Random soil moisture between 60 and 80
    prediction = predict_irrigation(temp, humidity, soil_moisture)
    if prediction is not None:
        add_new_data(temp, humidity, soil_moisture, prediction)

# Add specific data point for prediction
temp = 22
humidity = 56
soil_moisture = 75
prediction = predict_irrigation(temp, humidity, soil_moisture)
if prediction is not None:
    add_new_data(temp, humidity, soil_moisture, prediction)

# Display the data in tabular form
st.subheader("Sensor Data")
st.dataframe(data)

# Plot time series graphs for fluctuations
st.subheader("Sensor Data Fluctuations")

## Resample data for 15-second intervals
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

# Handle POST requests directly in Streamlit
query_params = st.query_params
if query_params:
    if 'body' in query_params:
        request = query_params
        response = handle_post_request(request)
        st.write(response)
