#define BLYNK_TEMPLATE_ID "TMPL2TnVz4vH9"
#define BLYNK_TEMPLATE_NAME "Smart Irrigation"
#define BLYNK_AUTH_TOKEN "osKAfPJ15zi-PIdeGskhreifuXXnBTWi"

#include <DHT.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <ThingSpeak.h>
#include <BlynkSimpleEsp32.h>
#include <HTTPClient.h>

// CHECK THE ESP32 PIN CONFIGURATION
#define LED 14
#define LDR 33

const char *RapiKey = "S2917S2WPFXVAEQY"; // Read API key from ThingSpeak
String WapiKey = "AH5UTONRL2M1W2J7"; // Write API key from ThingSpeak

// Channel Details
unsigned long channelID = 2570062; // Channel Id
const char *ssid = "Cliff'sA52s"; // wifi ssid and wpa2 key
const char *pass = "12345678";
const char* host = "api.thingspeak.com";
unsigned int fieldSoilMoisture = 1; // Field number for soil moisture
unsigned int fieldTemp = 2; // Field number for temperature
unsigned int fieldHum = 3; // Field number for humidity
const int updateInterval = 15000; // Update interval in milliseconds

WiFiClient client;
WiFiClient client2;

#define DHTPIN 27 // Pin where the DHT22 is connected
DHT dht(DHTPIN, DHT22);
int moisture_Pin = 35; // Soil Moisture Sensor input at Analog PIN VN on ESP32

// Blynk
char auth[] = "osKAfPJ15zi-PIdeGskhreifuXXnBTWi"; // Blynk auth token

void setup()
{
    Serial.begin(115200);
    delay(10);
    dht.begin();

    Serial.println("Connecting to ");
    Serial.println(ssid);

    WiFi.begin(ssid, pass);

    while (WiFi.status() != WL_CONNECTED)
    {
        delay(500);
        Serial.print(".");
    }
    Serial.println("");
    Serial.println("WiFi connected");

    // Initialize ThingSpeak
    ThingSpeak.begin(client2);

    // Initialize Blynk
    Blynk.begin(auth, ssid, pass);

    pinMode(LDR, INPUT);
    pinMode(LED, OUTPUT); // LED pin as output
}

void upload_data()
{
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    float soil_moisture = read_moisture();

    if (isnan(h) || isnan(t) || isnan(soil_moisture))
    {
        Serial.println("Failed to read from sensor!");
        return;
    }

    if (client.connect(host, 80)) // "184.106.153.149" or api.thingspeak.com
    {
        String postStr = WapiKey;
        postStr +="&field1=";
        postStr += String(soil_moisture);
        postStr +="&field2=";
        postStr += String(t);
        postStr +="&field3=";
        postStr += String(h);
        postStr += "\r\n\r\n";

        client.print("POST /update HTTP/1.1\n");
        client.print("Host: api.thingspeak.com\n");
        client.print("Connection: close\n");
        client.print("X-THINGSPEAKAPIKEY: " + WapiKey + "\n");
        client.print("Content-Type: application/x-www-form-urlencoded\n");
        client.print("Content-Length: ");
        client.print(postStr.length());
        client.print("\n\n");
        client.print(postStr);

        Serial.print("Soil Moisture: ");
        Serial.print(soil_moisture);
        Serial.print("%, Temperature: ");
        Serial.print(t);
        Serial.print(" degrees Celsius, Humidity: ");
        Serial.print(h);
        Serial.println("%. Publishing to ThingSpeak.");

        // Update Blynk
        Blynk.virtualWrite(V1, soil_moisture); // Virtual pin V1 for soil moisture
        Blynk.virtualWrite(V2, t); // Virtual pin V2 for temperature
        Blynk.virtualWrite(V3, h); // Virtual pin V3 for humidity
    }
    client.stop();

    Serial.println("Waiting...");

    // Send data to the Streamlit server
    send_data_to_server(t, h, soil_moisture);
}

void send_data_to_server(float temp, float humidity, float soil_moisture)
{
    if (WiFi.status() == WL_CONNECTED)
    {
        HTTPClient http;
        String serverPath = "https://capstone-project-final.streamlit.app/"; // Streamlit server IP and endpoint

        http.begin(serverPath);
        http.addHeader("Content-Type", "application/json");

        StaticJsonDocument<200> doc;
        doc["temp"] = temp;
        doc["humidity"] = humidity;
        doc["soil_moisture"] = soil_moisture;

        String requestBody;
        serializeJson(doc, requestBody);

        int httpResponseCode = http.POST(requestBody);

        if (httpResponseCode > 0)
        {
            String response = http.getString();
            Serial.println(httpResponseCode);
            Serial.println(response);
        }
        else
        {
            Serial.print("Error on sending POST: ");
            Serial.println(httpResponseCode);
        }
        http.end();
    }
    else
    {
        Serial.println("WiFi Disconnected");
    }
}

void loop()
{
    Blynk.run(); // Run Blynk

    int sdata = digitalRead(LDR);
    upload_data();
    delay(15);
    float value = fetchdata();
    Serial.print("Required soil moisture value: ");
    Serial.println(value);

    float curr_moisture = read_moisture(); // Read moisture data

    Serial.println("LDR Sensor value: ");
    Serial.print(sdata);
    Serial.println();

    if (curr_moisture < value) {
        Serial.print("Current soil moisture value is less than required soil moisture.");
        if (sdata == 1) {
            Serial.println("It is night");
            digitalWrite(LED, LOW);
            Serial.println("It's night, no need for irrigation... MOTOR OFF!!!!!!!");
        } else {
            Serial.println("It is day");
            digitalWrite(LED, HIGH); // turn the LED on
            Serial.println("!!!!! MOTOR ON !!!!!!!");
        }
    } else {
        Serial.print("Current soil moisture value is not less than required soil moisture.");
        Serial.println("Sufficient water in the field... MOTOR OFF!!!!!!!");
        digitalWrite(LED, LOW); // Initially LED is turned off
    }

    // Update Blynk with soil moisture value
    Blynk.virtualWrite(V1, curr_moisture); // Virtual pin V1 for soil moisture

    // ThingSpeak needs a minimum 15 sec delay between updates
    delay(10000);
}

float read_moisture()
{
    float moisture_value = (100.00 - ((analogRead(moisture_Pin) / 4095.00) * 100.00));
    Serial.print("Current soil moisture value: ");
    Serial.println(moisture_value);
    return moisture_value;
}

float fetchdata()
{
    float value = ThingSpeak.readFloatField(channelID, fieldSoilMoisture, RapiKey);
    return value;
}
