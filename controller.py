import requests
import urllib.request
import numpy as np
import joblib
import time
import json

# Path to the trained joblib ML model
model_path = r"/home/cjaure/Desktop/Capstone Project/CAPSTONE-PROJECT/new.joblib"

# Load the ML model
model = joblib.load(model_path)

def fetch_precipitation_data(api_key, city_name):
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city_name,
        "appid": api_key,
        "units": "metric"
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        precipitation = data.get("rain", {}).get("1h", 0)

        return precipitation
    else:
        print("Error: Unable to fetch precipitation data.")
        return None

def thingspeak_publish(val1):
    URL = 'https://api.thingspeak.com/update?api_key='
    KEY = 'AH5UTONRL2M1W2J7'
    HEADER = '&field4={val:.2f}'.format(val=val1)
    new_URL = URL + KEY + HEADER
    data = urllib.request.urlopen(new_URL)
    print(data.read())
    print("Successfully published")

def isnan(num):
    return num != num

result = [0.00, 0.00]
def thinkspeak_subscribe():
    # ThingSpeak API endpoint and parameters
    api_endpoint = "https://api.thingspeak.com/channels/2559239/feeds.json"
    api_key = "S2917S2WPFXVAEQY"  # ThingSpeak read API key
    results = 1   # Number of latest results to retrieve

    # Construct the API request URL
    api_url = "{}?api_key={}&results={}".format(api_endpoint, api_key, results)

    # Send GET request to the API
    response = requests.get(api_url)

    # Parse the response JSON
    data = json.loads(response.text)

    # Check if the API request was successful
    if response.status_code == 200:
        # Extract the latest temperature and humidity values
        entries = data["feeds"]
        print(entries)
        if len(entries) > 0:
            try:
                if entries[0].get("field1") is not None and entries[0].get("field2") is not None:  # ENTER YOUR FIELDS ACCORDINGLY TO THE THINKSPEAK CLOUD
                    result[0] = entries[0].get("field1")
                    result[1] = entries[0].get("field2")
            except Exception as e:
                print("Error parsing data: ", e)
        else:
            print("No data available.")
    else:
        print("Failed to fetch data. Error code:", response.status_code)

# OpenWeatherMap API key and the city name for the desired location
api_key = "ec6d96c7455825b76c80686bd4fb3ef7"  
city_name = "Harare"

while True:
    precipitation = fetch_precipitation_data(api_key, city_name)
    # Print the precipitation data
    if precipitation is not None:
        print(f"Precipitation: {precipitation} mm")

    thinkspeak_subscribe()
    print(f"Temperature: {result[0]} , Humidity: {result[1]}")

    # Preprocess the data
    # Check for the third input
    data = np.array([[result[0], result[1], 1, precipitation]])
    
    # Apply the ML model for prediction
    prediction = model.predict(data)
    prediction = float(prediction)
    print(f"Prediction: {prediction} %")
    
    thingspeak_publish(prediction)
    time.sleep(10)
