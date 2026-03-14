"""
HMI WebSocket → OPC UA Bridge
==============================
Sits between the browser-based HMI (hmi.html) and the OPC UA boiler simulator.
Browsers cannot speak OPC UA binary natively, so this bridge:
  - Accepts WebSocket connections from the HMI on ws://0.0.0.0:8765
  - Reads all sensor/actuator/alarm/simcontrol nodes from the OPC UA server
  - Accepts write commands from the HMI and forwards them to OPC UA

Protocol (JSON over WebSocket):
  Browser  → Bridge:  {"cmd": "read"}
                      {"cmd": "write", "node": "InletValve", "value": 50.0}
  Bridge   → Browser: {"type": "data",  "nodes": { "FillLevel": 80.1, ... }}
                      {"type": "error", "msg": "..."}

Run:
    pip install websockets asyncua
    python hmi_bridge.py

The OPC UA server (boiler_opcua_server.py) must be running first.
"""

import asyncio
import json
import logging
import os
from asyncua import Client
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("hmi-bridge")

import os

OPCUA_URL  = os.getenv("OPCUA_URL", "opc.tcp://localhost:4840/boiler/")
WS_HOST    = os.getenv("WS_HOST",   "0.0.0.0")
WS_PORT    = int(os.getenv("WS_PORT", "8765"))

# Map of friendly name → OPC UA browse path (relative to Objects/Boiler)
NODE_MAP = {
    # Actuators
    "InletValve":   "Actuators.InletValve",
    "OutletValve":  "Actuators.OutletValve",
    "HeaterEnable": "Actuators.HeaterEnable",
    # Sensors
    "FillLevel":    "Sensors.FillLevel",
    "Temperature":  "Sensors.Temperature",
    "Pressure":     "Sensors.Pressure",
    "FlowRateIn":   "Sensors.FlowRateIn",
    "FlowRateOut":  "Sensors.FlowRateOut",
    "HeaterPower":  "Sensors.HeaterPower",
    # Alarms
    "OverTemperature": "Alarms.OverTemperature",
    "LowLevel":        "Alarms.LowLevel",
    "HighPressure":    "Alarms.HighPressure",
    # SimControl
    "SimIntervalS": "SimControl.SimIntervalS",
    "SimSpeed":     "SimControl.SimSpeed",
}


class OpcUaBridge:
    def __init__(self):
        self.client     = None
        self.nodes      = {}   # name → asyncua Node object
        self.connected  = False

    async def connect(self):
        while True:
            try:
                self.client = Client(OPCUA_URL)
                await self.client.connect()
                log.info("Connected to OPC UA server at %s", OPCUA_URL)

                # Resolve all node objects once at connect time
                boiler = self.client.nodes.objects
                boiler = await boiler.get_child(["0:Boiler"])
                for name, path in NODE_MAP.items():
                    parts = ["0:" + p for p in path.split(".")]
                    self.nodes[name] = await boiler.get_child(parts)

                self.connected = True
                log.info("All %d nodes resolved", len(self.nodes))
                return

            except Exception as e:
                log.warning("OPC UA connect failed: %s — retry in 5s", e)
                self.connected = False
                await asyncio.sleep(5)

    async def read_all(self) -> dict:
        if not self.connected:
            return {}
        try:
            values = {}
            for name, node in self.nodes.items():
                val = await node.get_value()
                # Booleans stay bool; floats stay float
                values[name] = val
            return values
        except Exception as e:
            log.warning("Read error: %s", e)
            self.connected = False
            asyncio.create_task(self.reconnect())
            return {}

    async def write(self, name: str, value):
        if not self.connected or name not in self.nodes:
            return
        try:
            node = self.nodes[name]
            # Preserve the correct UA type
            existing = await node.get_value()
            if isinstance(existing, bool):
                value = bool(value)
            elif isinstance(existing, float):
                value = float(value)
            await node.set_value(value)
        except Exception as e:
            log.warning("Write error on %s: %s", name, e)

    async def reconnect(self):
        self.connected = False
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        await self.connect()


bridge = OpcUaBridge()


async def ws_handler(websocket):
    client_addr = websocket.remote_address
    log.info("HMI client connected: %s", client_addr)
    try:
        async for message in websocket:
            try:
                msg = json.loads(message)
            except json.JSONDecodeError:
                continue

            cmd = msg.get("cmd")

            if cmd == "read":
                values = await bridge.read_all()
                if values:
                    await websocket.send(json.dumps({"type": "data", "nodes": values}))
                else:
                    await websocket.send(json.dumps({"type": "error", "msg": "OPC UA not connected"}))

            elif cmd == "write":
                node  = msg.get("node")
                value = msg.get("value")
                if node and value is not None:
                    await bridge.write(node, value)

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        log.warning("WS handler error: %s", e)
    finally:
        log.info("HMI client disconnected: %s", client_addr)


async def main():
    # Connect to OPC UA first (retries indefinitely)
    await bridge.connect()

    # Start WebSocket server
    log.info("WebSocket HMI bridge listening on ws://%s:%d", WS_HOST, WS_PORT)
    async with websockets.serve(ws_handler, WS_HOST, WS_PORT):
        await asyncio.Future()   # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Bridge stopped.")
