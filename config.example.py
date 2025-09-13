# Configuration file for Pico Environmental Monitor
# Copy this file to config.py and update with your actual values

# WiFi Networks (tried in order)
WIFI_NETWORKS = [
    {"ssid": "YOUR_WIFI_SSID", "password": "YOUR_WIFI_PASSWORD"},
    {"ssid": "BACKUP_WIFI_SSID", "password": "BACKUP_WIFI_PASSWORD"}
]

# MQTT Broker Settings
MQTT_BROKER = "192.168.1.100"  # IP address of your MQTT broker
MQTT_PORT = 1883
MQTT_TOPIC = b"sensors/scd40"
CLIENT_ID = b"pico-scd40"