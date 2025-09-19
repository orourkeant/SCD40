# Raspberry Pi Pico Environmental Monitor

An environmental monitoring system using a Raspberry Pi Pico and SCD-40 sensor that measures CO2, temperature, and humidity, transmitting data via MQTT with comprehensive error handling and automatic recovery features.

## Features

- **Real-time Monitoring**: Measures CO2 (ppm), temperature (°C), and humidity (%) every 60 seconds
- **MQTT Communication**: Publishes data to configurable MQTT broker with automatic reconnection
- **WiFi Resilience**: Continuous WiFi monitoring and automatic reconnection with runtime recovery
- **Visual Status Indicators**: Enhanced LED patterns with continuous error feedback
- **Comprehensive Logging**: Timestamped error logging with startup vs runtime distinction
- **Automatic Recovery**: Self-healing WiFi and MQTT connections with diagnostic event publishing
- **Multi-Network WiFi**: Supports multiple WiFi networks with intelligent reconnection
- **Build Versioning**: Integrated version tracking with console display
- **Never-Give-Up Architecture**: Persistent reconnection attempts

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

## System Startup

On boot, the system displays build information:

```
==================================================
Environmental Monitoring System
Version: 1.0.3
Build Date: 2025-09-15
==================================================
```

This helps verify the correct version is running during development and deployment.

## LED Status Indicators

The onboard LED provides comprehensive visual feedback about system status:

| Pattern | Meaning | Description |
|---------|---------|-------------|
| Solid 5s | Startup | System initializing |
| Quick flash (100ms) | Normal operation | Flashes every 10 seconds during normal operation |
| **Continuous single blinks** | **WiFi Error** | **Active WiFi reconnection attempts** |
| **Continuous double blinks** | **MQTT Error** | **Active MQTT reconnection attempts** |
| 3 blinks + pause | Sensor Error | SCD-40 sensor not detected or failed |
| 4 blinks + pause | Runtime Error | Unexpected error in main loop |

### Enhanced Error Feedback

**Key Improvement**: Error patterns now provide continuous visual feedback during reconnection attempts, eliminating dead periods with no LED activity.

- **WiFi Issues**: Continuous single blinks throughout entire outage period
- **MQTT Issues**: Continuous double blinks during reconnection attempts
- **Immediate Feedback**: LED activity starts instantly when problems are detected
- **Clear Distinction**: Different patterns make it obvious which system has issues

### WiFi Recovery Behavior

The system treats WiFi connectivity as critical (device is useless without it):

- **Never Gives Up**: Continues WiFi reconnection attempts indefinitely
- **Runtime Monitoring**: Checks WiFi status every cycle, not just at startup
- **Intelligent Reconnection**: Remembers successful network and reconnects to same one
- **Continuous Feedback**: LED shows single blinks throughout entire reconnection process
- **Priority Handling**: WiFi issues take priority over MQTT operations
- **Error Logging**: Distinguishes between startup failures and runtime disconnections

### MQTT Recovery Behavior

When MQTT connection is lost:
- LED shows continuous double blinks during reconnection attempts
- System attempts reconnection every 5 seconds
- Diagnostic events published to `sensors/scd40/events` topic upon successful reconnection
- Normal operation resumes automatically when connection is restored
- MQTT reconnection is suspended when WiFi is down (WiFi takes priority)

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

Errors are automatically logged to `error.log` with timestamps and context:

**Startup vs Runtime Distinction:**
```
[00:02:15] WiFi connection failed - all networks exhausted
[00:15:23] WiFi connection lost - attempting reconnection to MyNetwork
[00:15:28] WiFi reconnection failed to MyNetwork
[00:15:33] MQTT connection failed: [Errno 113] ECONNABORTED
[00:15:38] MQTT reconnection failed: [Errno 113] ECONNABORTED
```

This helps distinguish between configuration issues (startup) and runtime network problems.

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

### Data Persistence Configuration

**Important**: The dashboard is configured with persistent storage to survive Node-RED restarts.

**Configuration Required:**
1. Edit your Node-RED `settings.js` file:
   ```javascript
   contextStorage: {
       default: {
           module: "localfilesystem"
       }
   }
   ```

2. Restart Node-RED: `sudo systemctl restart nodered`

**Behavior:**
- **Historical data survives restarts**: 24-hour trend charts retain data through Node-RED crashes/restarts
- **24-hour retention still applies**: Data older than 24 hours is automatically discarded  
- **Gradual recovery**: Charts rebuild from saved data rather than starting empty
- **Storage location**: Data stored in `~/.node-red/context/` directory

**Impact:**
- **Before configuration**: Node-RED restarts result in empty trend charts
- **After configuration**: Charts retain whatever historical data was saved to disk

## File Structure

```
pico-environmental-monitor/
├── main.py              # Main application code with versioning
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
1. **LED startup indicator** (5 seconds solid)
2. **Version display** (console output with build info)
3. **WiFi connection attempt** (tries all configured networks in order)
4. **Network memory** (remembers which network succeeded)
5. **MQTT broker connection**
6. **SCD-40 sensor initialization**
7. **Begin main monitoring loop**

### Main Loop Operation
1. **WiFi Priority Check**: Monitors WiFi status first (highest priority)
2. **MQTT Status Check**: Monitors MQTT connection (when WiFi is OK)
3. **Normal Mode**: 60-second cycle with sensor readings and MQTT publishing
4. **Error Recovery Modes**: Dedicated reconnection states with continuous LED feedback
5. **Visual Feedback**: LED patterns indicate current system state
6. **Logging**: All errors timestamped and logged with context

### Recovery Strategy
- **Priority System**: WiFi recovery takes precedence over MQTT
- **Persistent**: Never gives up on WiFi reconnection (device useless without it)
- **Intelligent**: Reconnects to known-good network, not cycling through all networks
- **Non-blocking**: Continuous LED feedback during all recovery attempts
- **Diagnostic**: Publishes reconnection events for monitoring
- **Context-Aware**: Error logging distinguishes startup vs runtime issues

### Network Behavior
- **Startup**: Tries all configured networks in order, remembers successful one
- **Runtime**: Only attempts reconnection to the network that worked at startup
- **Location Changes**: Requires restart to discover new networks (by design)
- **Resilience**: Handles temporary outages, long outages, and intermittent connectivity

## Troubleshooting

### Common Issues

**WiFi Connection Fails at Startup**
- Check SSID and password in `config.py`
- Ensure WiFi network is 2.4GHz (Pico W limitation)
- Verify network is in range
- LED shows continuous single blinks, never stops trying

**WiFi Drops During Operation**
- Normal behavior - system will reconnect automatically
- LED shows continuous single blinks during reconnection
- Check `error.log` for "WiFi connection lost" messages
- System attempts reconnection to same network that worked at startup

**MQTT Connection Fails**
- Verify broker IP address and port in `config.py`
- Check if broker is running: `sudo systemctl status mosquitto`
- LED shows continuous double blinks during reconnection attempts
- Ensure firewall allows connections on MQTT port

**Sensor Not Detected**
- Verify I2C wiring (SDA=GPIO0, SCL=GPIO1)
- Check sensor power supply (3.3V)
- LED shows 3 blinks + pause pattern
- Confirm sensor address (0x62) with I2C scan

**No Data Publishing**
- SCD-40 requires ~60 seconds warm-up for first reading
- Check `error.log` for detailed error information
- Monitor `sensors/scd40/events` topic for diagnostic messages
- Verify both WiFi and MQTT are connected (check LED patterns)

### LED Pattern Diagnosis

**Continuous Single Blinks**: WiFi problem
- Check WiFi router is powered and in range
- Verify credentials in `config.py`
- System will never stop trying to reconnect

**Continuous Double Blinks**: MQTT problem
- Check MQTT broker is running
- Verify broker IP address in config
- Test with: `mosquitto_sub -h YOUR_BROKER_IP -t sensors/scd40`

**4 Blinks + Long Pause**: Runtime error
- Check `error.log` for exception details
- May indicate sensor issues or code problems

### Monitoring Commands

Check MQTT data:
```bash
# Subscribe to sensor data
mosquitto_sub -h YOUR_BROKER_IP -t "sensors/scd40"

# Subscribe to diagnostic events
mosquitto_sub -h YOUR_BROKER_IP -t "sensors/scd40/events"

# Check MQTT broker status
sudo systemctl status mosquitto

# Test MQTT broker connectivity
mosquitto_pub -h YOUR_BROKER_IP -t test -m "hello"
```

## Development

### Version Control
Each build includes version tracking:
- Header comments show full version info
- Console displays version banner on startup
- Single line comment above imports for quick reference
- Use semantic versioning: major.minor.patch (1.0.3, 1.0.4, etc.)

### Adding Features
- Error handling follows established patterns with logging and LED codes
- New features should integrate with existing recovery mechanisms
- Maintain non-blocking operation during error conditions
- WiFi takes priority over all other operations
- Use continuous LED patterns for active error states

### Testing Recovery Scenarios

**WiFi Recovery Testing:**
1. Start system with WiFi connected
2. Turn off WiFi router or use mobile hotspot
3. Observe continuous single blinks immediately
4. Turn WiFi back on - system should reconnect automatically
5. Verify normal operation resumes (single flash every 10 seconds)

**MQTT Recovery Testing:**
1. Start system with MQTT broker running
2. Stop MQTT broker: `sudo systemctl stop mosquitto`
3. Observe continuous double blinks during reconnection attempts
4. Restart broker: `sudo systemctl start mosquitto`
5. Verify automatic reconnection and diagnostic event publishing

**Priority Testing:**
1. Disconnect both WiFi and MQTT
2. Should see WiFi error pattern (single blinks) only
3. Reconnect WiFi - should automatically reset MQTT state
4. Verify normal operation resumes

## License

This project is open source. Feel free to modify and distribute according to your needs.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with proper version increments
4. Test thoroughly (especially error recovery scenarios)
5. Update README if adding new features
6. Submit a pull request

## Changelog

### v1.0.3
- **Enhanced WiFi Recovery**: Continuous runtime WiFi monitoring and reconnection
- **Improved LED Feedback**: Continuous error patterns eliminate dead time
- **Priority System**: WiFi takes precedence over MQTT operations
- **Build Versioning**: Integrated version display and tracking
- **Better Error Logging**: Distinguishes startup vs runtime issues
- **Never-Give-Up Architecture**: Persistent WiFi reconnection (device useless without connectivity)

### v1.0.2
- Enhanced LED error patterns with continuous feedback
- Build information display system
- Improved error state handling

### v1.0.1
- WiFi retry capability and runtime monitoring
- Continuous LED error feedback during reconnection attempts

### v1.0.0
- Initial release with basic sensor monitoring
- MQTT publishing with automatic reconnection
- Comprehensive error handling and logging
- LED status indicators
- Multi-network WiFi support
- Git version control integration
