# Phase 3: ESP32 Firmware (Person E)

## Hardware BOM

| Part | Model | Count | Notes |
|------|-------|-------|-------|
| Microcontroller | ESP32-WROOM-32 | 1 | $10, WiFi + BLE |
| CAN Transceiver | SN65HVD230 | 1 | 3.3V, TI Texas Instruments |
| CAN Connector | 9-pin Deutsch | 1 | Type-1 (black) = 250K, Type-2 (green) = 500K |
| Resistors | 120Ω 1/4W | 2 | Termination (measure 60Ω across CAN H/L) |
| Capacitors | 100nF ceramic | 2 | Decoupling |
| Power | 5V USB or DC | 1 | Supply |

## Wiring

```
J1939 CAN Bus (Deutsch 9-pin Type-1 250K)
    ├─ Pin 1: CAN_H → SN65HVD230 pin 7 (CANH)
    ├─ Pin 3: GND → SN65HVD230 pin 2 (GND), ESP32 GND
    ├─ Pin 9: CAN_L → SN65HVD230 pin 8 (CANL)
    └─ (Pins 2,4,5,6,7,8: reserved/shielded)

SN65HVD230 → ESP32
    ├─ pin 1 (RXD) → GPIO 4 (TWAI RX)
    ├─ pin 3 (TXD) → GPIO 5 (TWAI TX)
    ├─ pin 2,6 (GND) → ESP32 GND
    └─ pin 8 (VCC) → 3.3V

120Ω Termination (on CAN H/L pair at far end of bus)
```

## Build & Flash

### 1. Setup
```bash
cd firmware
pip install platformio
```

### 2. Configure
Edit `platformio.ini`:
```ini
[env:esp32dev]
platform = espressif32
board = esp32dev
framework = arduino
monitor_speed = 115200
lib_deps =
  ArduinoJson@^7.0
  ESP Async WebServer
  ESP32 CAN
```

### 3. Build
```bash
pio run
```

### 4. Flash
```bash
pio run -t upload
```

### 5. Monitor
```bash
pio device monitor
```

Should print:
```
CAN Vision ESP32 started
AP Mode: CANVision_XXXX | 192.168.4.1:81
Waiting for CAN frames...
```

## Code Structure

```cpp
// firmware/src/main.cpp
#include <esp_can.h>
#include <ESPAsyncWebServer.h>
#include <ArduinoJson.h>

void setup() {
  Serial.begin(115200);
  setupWiFiAP();       // Create hotspot
  setupTWAI();         // CAN 250K
  startWebSocket();    // Port 81
}

void loop() {
  readCANFrames();     // TWAI receive
  broadcastFrames();   // WebSocket send
}
```

## TWAI Config

```cpp
const twai_general_config_t g_config = TWAI_GENERAL_CONFIG_DEFAULT(
  GPIO_NUM_5,    // TX
  GPIO_NUM_4,    // RX
  TWAI_MODE_LISTEN_ONLY);

const twai_timing_config_t t_config = 
  TWAI_TIMING_CONFIG_250KBITS();  // 250K default

const twai_filter_config_t f_config = 
  TWAI_FILTER_CONFIG_ACCEPT_ALL();

twai_driver_install(&g_config, &t_config, &f_config);
twai_start();
```

## WiFi AP Config

```cpp
void setupWiFiAP() {
  WiFi.softAP("CANVision_" + String(random(0xFFFF), HEX),
              "password123");  // SSID, password
  
  IPAddress IP(192, 168, 4, 1);
  IPAddress NMask(255, 255, 255, 0);
  WiFi.softAPConfig(IP, IP, NMask);
  
  Serial.println("AP started: " + String(WiFi.softAPSSID()));
  Serial.println("IP: " + String(IP));
}
```

## WebSocket Frame Format

```json
{
  "ts": 1717000000.020,
  "arbitration_id": 207871904,
  "arbitration_id_hex": "0x0CF00400",
  "is_extended_id": true,
  "dlc": 8,
  "data": [17, 98, 235, 240, 255, 255, 255, 255],
  "channel": 0
}
```

---

## Testing

1. **No CAN bus**: Loop back TXD to RXD for self-test
2. **Real bus**: Connect to J1939 vehicle, monitor serial output
3. **Browser**: Open http://192.168.4.1 → should connect, stream frames

---

## Future

- CAN FD support (ESP32-S3)
- Bitrate selector (250K, 500K, 1M)
- Address claiming (active mode)
- Transmit support (advanced users)

---

Files to create: `firmware/src/main.cpp`, `platformio.ini`
