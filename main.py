import time
import network
import json
import sys
from machine import I2C, Pin
from umqtt.simple import MQTTClient
from scd40 import SCD40
from config import WIFI_NETWORKS, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, CLIENT_ID

# ---------------- LOGGING ----------------
def log_error(message):
    """
    Log error message to error.log with timestamp
    Creates file if it doesn't exist, otherwise appends
    """
    try:
        # Get current time since boot (seconds)
        current_time = time.ticks_ms() // 1000
        hours = current_time // 3600
        minutes = (current_time % 3600) // 60
        seconds = current_time % 60
        
        timestamp = "[{:02d}:{:02d}:{:02d}]".format(hours, minutes, seconds)
        log_entry = "{} {}\n".format(timestamp, message)
        
        with open("error.log", "a") as f:
            f.write(log_entry)
            
    except Exception as e:
        # If logging fails, print to console as fallback
        print("ERROR: Failed to write to log:", str(e))

# ---------------- LED SETUP ----------------
led = Pin('LED', Pin.OUT)

def led_startup():
    """Solid on for 5 seconds"""
    led.on()
    time.sleep(5)
    led.off()

def led_error(code):
    """Flash error code repeatedly: code blinks + 1 sec break"""
    while True:
        for _ in range(code):
            led.on()
            time.sleep(0.2)  # Short blink
            led.off()
            time.sleep(0.2)
        time.sleep(1)  # 1 second break

def led_normal_flash():
    """Quick flash: 100ms on"""
    led.on()
    time.sleep(0.1)
    led.off()

def led_error_pattern(code):
    """Show error code pattern once: code blinks + 1 sec break"""
    for _ in range(code):
        led.on()
        time.sleep(0.2)  # Short blink
        led.off()
        time.sleep(0.2)
    time.sleep(1)  # 1 second break

# ---------------- MQTT RECONNECTION ----------------
def mqtt_reconnect_attempt(wlan):
    """
    Attempt single MQTT reconnection
    Returns True if successful, False if failed
    """
    global client
    
    # Check WiFi status first
    if not wlan.isconnected():
        print("WiFi down - cannot attempt MQTT reconnection")
        return False
    
    try:
        client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT)
        client.connect()
        print("MQTT reconnected successfully")
        return True
        
    except Exception as e:
        print("MQTT reconnection failed: {}".format(str(e)))
        log_error("MQTT reconnection failed: {}".format(str(e)))
        return False

# ---------------- STARTUP ----------------
led_startup()

# ---------------- CONNECT WIFI ----------------
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    
    for network_info in WIFI_NETWORKS:
        ssid = network_info["ssid"]
        password = network_info["password"]
        
        print(f"\nTrying to connect to {ssid}...")
        print(f"Initial WiFi status: {wlan.status()}")
        
        # Attempt connection
        wlan.connect(ssid, password)
        print(f"Connection initiated, status: {wlan.status()}")
        
        timeout = 15
        start_time = time.time()
        
        while not wlan.isconnected():
            current_status = wlan.status()
            elapsed = time.time() - start_time
            
            if elapsed > timeout:
                print(f"\nTimeout after {timeout}s connecting to {ssid}")
                print(f"Final status: {current_status}")
                break
                
            # Log status changes
            if int(elapsed) % 3 == 0 and elapsed > 0:  # Every 3 seconds
                print(f"\n[{elapsed:.0f}s] Status: {current_status}", end="")
            else:
                print(".", end="")
            time.sleep(0.5)
        
        if wlan.isconnected():
            print(f"\nSuccessfully connected to {ssid}")
            print(f"IP config: {wlan.ifconfig()}")
            print(f"Final status: {wlan.status()}")
            return wlan
        else:
            print(f"Failed to connect to {ssid}")
    
    print("\nAll WiFi networks failed!")
    log_error("WiFi connection failed - all networks exhausted")
    return None

wlan = connect_wifi()
if not wlan:
    led_error(1)  # Error code 1 - WiFi failed

# ---------------- CONNECT MQTT ----------------
try:
    client = MQTTClient(CLIENT_ID, MQTT_BROKER, MQTT_PORT)
    client.connect()
    print("Connected to MQTT broker:", MQTT_BROKER)
except Exception as e:
    print("MQTT connection failed:", e)
    log_error("MQTT connection failed: {}".format(str(e)))
    led_error(2)  # Error code 2 - MQTT failed

# ---------------- SENSOR INIT ----------------
try:
    i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100_000)
    devices = i2c.scan()
    if 0x62 not in devices:
        print("SCD-40 not found on I2C bus!")
        log_error("SCD-40 not found on I2C bus - devices found: {}".format(devices))
        led_error(3)  # Error code 3 - Sensor not found
    else:
        print("SCD-40 detected.")
        sensor = SCD40(i2c)
        sensor.start_periodic_measurement()
        print("Started periodic measurement...")
except Exception as e:
    print("Sensor initialization failed:", e)
    log_error("Sensor initialization failed: {}".format(str(e)))
    led_error(3)  # Error code 3 - Sensor failed

print("All systems ready - starting main loop")

# ---------------- MAIN LOOP ----------------
mqtt_error_state = False
reconnect_attempt_count = 0

while True:
    try:
        # Handle MQTT error state
        if mqtt_error_state:
            # Show error LED pattern
            led_error_pattern(2)
            
            # Attempt reconnection
            if mqtt_reconnect_attempt(wlan):
                # Success! Send event and reset state
                reconnect_attempt_count += 1
                success_msg = json.dumps({
                    "event": "mqtt_reconnected",
                    "attempts": reconnect_attempt_count
                })
                try:
                    client.publish(b"sensors/scd40/events", success_msg)
                    print("MQTT reconnection successful - resuming normal operation")
                    mqtt_error_state = False
                    reconnect_attempt_count = 0
                except:
                    # If event publish fails, we're still in error state
                    pass
            else:
                # Failed, increment counter and wait
                reconnect_attempt_count += 1
            
            # Wait 5 seconds before next attempt
            time.sleep(5)
            continue
        
        # Normal operation - 60 second cycle with LED flash every 10 seconds
        for i in range(6):
            led_normal_flash()
            time.sleep(10)
        
        # Take sensor reading and publish
        result = sensor.read_measurement()
        if result:
            co2, temp, rh = result
            temp = round(temp, 2)
            rh = round(rh, 2)
            payload = json.dumps({
                "co2": co2,
                "temp": temp,
                "rh": rh
            })
            
            try:
                client.publish(MQTT_TOPIC, payload)
                print("Published:", payload)
            except Exception as e:
                print("MQTT publish failed:", e)
                log_error("MQTT publish failed: {}".format(str(e)))
                mqtt_error_state = True
                reconnect_attempt_count = 0
        else:
            print("Waiting for valid data...")
            try:
                waiting_msg = json.dumps({"event": "sensor_waiting_for_data"})
                client.publish(b"sensors/scd40/events", waiting_msg)
            except Exception as e:
                print("Failed to publish sensor waiting event:", e)
                log_error("MQTT publish failed: {}".format(str(e)))
                mqtt_error_state = True
                reconnect_attempt_count = 0
            
    except Exception as e:
        print("Error in main loop:", e)
        log_error("Main loop error: {}".format(str(e)))
        led_error(4)  # Error code 4 - Runtime error