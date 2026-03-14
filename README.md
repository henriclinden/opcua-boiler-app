# Boiler HMI

A browser-based High-Performance HMI for the [boiler-simulator](https://github.com/henriclinden/opcua-boiler-sim) OPC UA server. Follows ISA 101 / HP-HMI design philosophy: gray background, color reserved for abnormal states, analog arc gauges with moving pointers, standard P&ID instrument symbols, and a live process trend.

NOTE: Designed for use with the unauthenticated boiler-simulator. Do not connect to production systems.

---

## Features

- Full P&ID view with ISA instrument circles (TT-01, PT-01, LT-01, FI-101, FI-201)
- Standard butterfly valve symbols with flow indication
- Analog arc gauges (Temperature, Pressure, Level) with normal/Hi/HiHi bands and moving pointer
- Flashing alarm banner for OverTemperature, LowLevel, HighPressure
- Actuator faceplates: sliders for InletValve and OutletValve, toggle for HeaterEnable
- 120-second rolling process trend (Temperature, Level, Pressure)
- Live SimControl sliders (SimIntervalS, SimSpeed) — adjusts simulator speed in real time
- **Demo mode** — falls back to a built-in JS physics simulation when the bridge is unreachable

---

## Architecture

```
 Browser (hmi.html)
       │  WebSocket JSON  ws://<host>:8765
       ▼
 hmi_bridge.py          ← This project
       │  OPC UA binary  opc.tcp://<simulator-host>:4840/boiler/
       ▼
 boiler-simulator       ← Separate project
```

Browsers cannot speak OPC UA binary natively. `hmi_bridge.py` is a lightweight WebSocket↔OPC UA gateway that runs alongside the static HMI file.

---

## Requirements

- Python 3.8+
- [asyncua](https://github.com/FreeOpcUa/opcua-asyncio)
- [websockets](https://websockets.readthedocs.io/)

```bash
pip install -r requirements.txt
```

---

## Getting Started

### 1. Start the simulator (separate repo)

```bash
cd ../boiler-simulator
python boiler_opcua_server.py
```

### 2. Start the WebSocket bridge

```bash
git clone https://github.com/your-username/boiler-hmi.git
cd boiler-hmi
pip install -r requirements.txt
python hmi_bridge.py
```

### 3. Open the HMI

Serve `hmi.html` from any static file server:

```bash
python -m http.server 8080
```

Then open [http://localhost:8080/hmi.html](http://localhost:8080/hmi.html) in your browser.

---

## Configuration

The bridge is configured via environment variables:

| Variable | Default | Description |
|---|---|---|
| `OPCUA_URL` | `opc.tcp://localhost:4840/boiler/` | Address of the OPC UA simulator |
| `WS_HOST` | `0.0.0.0` | WebSocket listen address |
| `WS_PORT` | `8765` | WebSocket listen port |

Example — simulator running on a separate device:

```bash
OPCUA_URL=opc.tcp://192.168.1.50:4840/boiler/ python hmi_bridge.py
```

---

## Docker deployment

Both the bridge and the static HMI file server run in one container.

```bash
# Build and start
docker compose up -d

# Open the HMI
# http://<host-ip>:8080/hmi.html

# Follow logs
docker compose logs -f

# Stop
docker compose down
```

### Connecting to a remote simulator

If the boiler-simulator runs on a separate host or container, set `OPCUA_URL` in `docker-compose.yml`:

```yaml
environment:
  - OPCUA_URL=opc.tcp://192.168.1.50:4840/boiler/
```

### Running both projects on the same Docker host

Create a shared network so the HMI bridge can reach the simulator by container name:

```bash
docker network create boiler-net

# In boiler-simulator/
docker compose --project-name boiler-sim up -d --network boiler-net

# In boiler-hmi/ — uncomment the networks block in docker-compose.yml, then:
docker compose --project-name boiler-hmi up -d
```

### Cross-compiling for ARM (Raspberry Pi, embedded boards)

```bash
docker buildx create --use

# ARM 64-bit (Pi 4, Pi 5)
docker buildx build --platform linux/arm64 -t boiler-hmi:latest --load .

# Transfer to device
docker save boiler-hmi:latest | ssh user@<device-ip> docker load
```

---

## HP-HMI Design Principles Applied

| Principle | Implementation |
|---|---|
| Gray background | `#dddddd` (Gray 3) throughout — no dark themes, no gradients |
| Color for abnormal only | Screen is near-monochrome during normal operation; yellow = Hi/Lo, red = HiHi/LoLo |
| Analog indicators | Arc gauges with moving needle, banded normal/Hi/HiHi zones |
| Live data in bold dark blue | All process values use `#003399` |
| Static labels in dark gray | Tag names and units are muted, never competing with live data |
| Line weight over color | 3 px main process lines, 1 px secondary — weight encodes importance |
| Left-to-right process flow | CWS inlet enters left → boiler → hot water outlet exits right |
| ISA instrument symbols | Standard circle tags (TT, PT, LT, FI) with dashed signal lines |

---

## Project Structure

```
.
├── hmi.html          # Browser-based High-Performance HMI (single file, no build step)
├── hmi_bridge.py     # WebSocket ↔ OPC UA bridge
├── requirements.txt  # Python dependencies (asyncua, websockets)
├── Dockerfile        # Bridge + static file server
├── docker-compose.yml
├── .dockerignore
└── README.md
```

---

## Related Projects

- [boiler-simulator](https://github.com/your-username/boiler-simulator) — OPC UA boiler simulator this HMI connects to

---

## License

MIT License. See [LICENSE](LICENSE) for details.
