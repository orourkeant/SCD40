# Raspberry Pi Pico Environmental Monitor

A robust environmental monitoring system using a Raspberry Pi Pico and SCD-40 sensor that measures CO2, temperature, and humidity, transmitting data via MQTT with comprehensive error handling and automatic recovery features.

## Features

- **Real-time Monitoring**: Measures CO2 (ppm), temperature (°C), and humidity (%) every 60 seconds
- **MQTT Communication**: Publishes data to configurable MQTT broker with automatic reconnection
- **Visual Status Indicators**: LED patterns indicate system status and error conditions
- **Comprehensive Logging**: Timestamped error logging to local file system
- **Automatic Recovery**: Self-healing MQTT connections with diagnostic event publishing
- **Multi-Network WiFi**: Supports multiple WiFi networks with automatic failover
- **Version Controlled**: Git-ready with proper credential protection

## Hardware Requirements

- **Raspberry Pi Pico W** (with WiFi capability)
- **SCD-40 CO2/Temperature/Humidity Sensor** (Sensirion)
- **I2C Connection**: 
  - SDA → GPIO 0 (Pin 1)
  - SCL → GPIO 1 (Pin 2)
  - VCC → 3.3V
  - GND → Ground

## Software Requirements

- **MicroPython** firmware on Raspberry Pi Pico W
- **umqtt.simple** library (usually included with MicroPython)
- **SCD40 driver library** (included in project)
- **MQTT Broker** (e.g., Mosquitto, Node-RED)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/pico-environmental-monitor.git
   cd pico-environmental-monitor
   ```

2. **Set up configuration:**
   ```bash
   cp config.example.py config.py
   ```
   Edit `config.py` with your WiFi and MQTT settings.

3. **Upload files to Pico:**
   - Copy all `.py` files to the Pico's root directory
   - Ensure the SCD40 library is available

4. **Run the system:**
   - Reset the Pico or run `main.py`

## Configuration

Edit `config.py` with your specific settings:

```python
# WiFi Networks (tried in order)
WIFI_NETWORKS = [
    {"ssid": "YOUR_WIFI_SSID", "password": "YOUR_WIFI_PASSWORD"},
    {"ssid": "BACKUP_WIFI_SSID", "password": "BACKUP_WIFI_PASSWORD"}
]

# MQTT Broker Settings
MQTT_BROKER = "192.168.1.100"  # Your MQTT broker IP
MQTT_PORT = 1883
MQTT_TOPIC = b"sensors/scd40"
CLIENT_ID = b"pico-scd40"
```

## LED Status Indicators

The onboard LED provides visual feedback about system status:

| Pattern | Meaning | Description |
|---------|---------|-------------|
| Solid 5s | Startup | System initializing |
| Quick flash (100ms) | Normal operation | Flashes every 10 seconds during normal operation |
| 1 blink + pause | WiFi Error | Cannot connect to any configured WiFi network |
| 2 blinks + pause | MQTT Error | MQTT broker connection failed or lost |
| 3 blinks + pause | Sensor Error | SCD-40 sensor not detected or failed |
| 4 blinks + pause | Runtime Error | Unexpected error in main loop |

### MQTT Recovery Behavior

When MQTT connection is lost:
- LED shows error pattern 2 (double blink) every 5 seconds
- System attempts reconnection every 5 seconds
- Diagnostic events published to `sensors/scd40/events` topic upon successful reconnection
- Normal operation resumes automatically when connection is restored

## Data Format

### Sensor Data
Published to configured `MQTT_TOPIC` (default: `sensors/scd40`):
```json
{
  "co2": 412,
  "temp": 23.45,
  "rh": 55.32
}
```

### Diagnostic Events
Published to `sensors/scd40/events`:
```json
{
  "event": "mqtt_reconnected",
  "attempts": 5
}
```

```json
{
  "event": "sensor_waiting_for_data"
}
```

## Error Logging

Errors are automatically logged to `error.log` with timestamps:
```
[00:15:23] MQTT connection failed: [Errno 113] ECONNABORTED
[00:15:28] MQTT reconnection failed: [Errno 113] ECONNABORTED
[00:15:45] MQTT reconnected successfully
```

## Node-RED Dashboard Setup

The project includes a complete Node-RED dashboard flow for visualizing the sensor data.

### Prerequisites
- Node-RED installed
- `node-red-dashboard` palette installed
- Access to MQTT broker

### Installation
1. **Import the flow:**
   - Copy the contents of `flows.json`
   - In Node-RED: Menu → Import → Clipboard
   - Paste the flow and click Import

2. **Configure MQTT broker:**
   - Double-click the MQTT input node
   - Update broker IP address to match your setup
   - Deploy the flow

3. **Access dashboard:**
   - Navigate to `http://your-node-red-ip:1880/ui`
   - View real-time gauges and 24-hour trend charts

### Dashboard Features
- **Real-time Gauges**: Live CO2, temperature, and humidity readings
- **24-Hour Trends**: Historical charts with hourly averages
- **Automatic Data Storage**: In-memory storage with 24-hour retention
- **Color-coded Alerts**: Gauge colors indicate normal/warning/critical levels

### Dashboard Layout
- **CO2 Gauge**: 0-2500 ppm range with traffic light colors
- **Temperature Gauge**: 0-50°C range
- **Humidity Gauge**: 0-100% range
- **Trend Charts**: Three separate 24-hour historical views

## File Structure

```
pico-environmental-monitor/
├── main.py              # Main application code
├── scd40.py            # SCD-40 sensor driver
├── config.example.py   # Configuration template
├── config.py           # Your configuration (git-ignored)
├── flows.json          # Node-RED dashboard flow
├── error.log           # Runtime error log (git-ignored)
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## System Architecture

### Initialization Sequence
1. LED startup indicator (5 seconds solid)
2. WiFi connection attempt (tries all configured networks)
3. MQTT broker connection
4. SCD-40 sensor initialization
5. Begin main monitoring loop

### Main Loop Operation
1. **Normal Mode**: 60-second cycle with sensor readings and MQTT publishing
2. **Error Recovery Mode**: When MQTT fails, enters 5-second reconnection cycle
3. **Visual Feedback**: LED patterns indicate current system state
4. **Logging**: All errors timestamped and logged locally

### Recovery Strategy
- **Non-blocking**: System continues operation during recovery attempts
- **Persistent**: Keeps trying to reconnect until successful
- **Diagnostic**: Publishes reconnection events for monitoring
- **Visual**: LED feedback shows recovery attempts in progress

## Troubleshooting

### Common Issues

**WiFi Connection Fails**
- Check SSID and password in `config.py`
- Ensure WiFi network is 2.4GHz (Pico W limitation)
- Verify network is in range

**MQTT Connection Fails**
- Verify broker IP address and port
- Check if broker is running and accessible
- Ensure firewall allows connections on MQTT port

**Sensor Not Detected**
- Verify I2C wiring (SDA=GPIO0, SCL=GPIO1)
- Check sensor power supply (3.3V)
- Confirm sensor address (0x62) with I2C scan

**No Data Publishing**
- SCD-40 requires ~60 seconds warm-up for first reading
- Check `error.log` for detailed error information
- Monitor `sensors/scd40/events` topic for diagnostic messages

### Monitoring Commands

Check MQTT data:
```bash
# Subscribe to sensor data
mosquitto_sub -h YOUR_BROKER_IP -t "sensors/scd40"

# Subscribe to diagnostic events
mosquitto_sub -h YOUR_BROKER_IP -t "sensors/scd40/events"
```

## Development

### Adding Features
- Error handling follows established patterns with logging and LED codes
- New features should integrate with existing recovery mechanisms
- Maintain non-blocking operation during error conditions

### Testing Recovery
1. Start system with MQTT broker running
2. Stop MQTT broker to trigger error state
3. Observe LED error pattern 2 (double blink every 5 seconds)
4. Restart broker and verify automatic reconnection
5. Check diagnostic events are published upon recovery

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (especially error recovery scenarios)
5. Submit a pull request

## Changelog

### v1.0.0
- Initial release with basic sensor monitoring
- MQTT publishing with automatic reconnection
- Comprehensive error handling and logging
- LED status indicators
- Multi-network WiFi support
- Git version control integration