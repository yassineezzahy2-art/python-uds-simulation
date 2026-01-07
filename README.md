# Automotive UDS Secure Flashing Simulator 🚗💻

## 📝 Overview
This project is a complete simulation of an **Automotive Diagnostic Stack** based on the **ISO-14229 (UDS)** standard.
It simulates the interaction between a **Tester (Client)** and an **ECU (Server)** over a Virtual CAN Bus (SocketCAN).

The main goal was to reverse-engineer and implement the critical **Secure Flashing Sequence** used in the automotive industry to update ECU firmware.

## 🚀 Key Features
* **ISO-TP Implementation:** Manual handling of CAN frames, including segmentation and PCI byte parsing.
* **Security Access (Service 0x27):** Implementation of a **Seed & Key** authentication algorithm (Bitwise operations) to unlock the ECU.
* **Firmware Flashing Sequence:** Full simulation of the download process:
    * `0x10` Diagnostic Session Control (Extended Session)
    * `0x27` Security Access (Unlock)
    * `0x34` Request Download
    * `0x36` Transfer Data (Block by Block)
    * `0x37` Request Transfer Exit
* **ECU Reset (Service 0x11):** Simulating a reboot after a successful flash.
* **Error Handling:** Implementation of Negative Response Codes (NRC) like `0x35` (Invalid Key) or `0x33` (Security Access Denied).

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Communication:** Linux SocketCAN (`can-raw`)
* **Protocol:** ISO-14229 (UDS) / ISO-15765 (ISO-TP)
* **Interface:** Virtual CAN (`vcan0`)

## 📂 Project Structure
* `flash_tool.py`: The Tester tool that orchestrates the flashing sequence.
* `ecu_sim.py`: The ECU simulator that responds to requests and validates security keys.
* `uds_algo.py`: The shared Seed/Key algorithm logic.
* `client.py` / `ecu_server.py`: Legacy UDS communication scripts.

## ⚡ How to Run

### 1. Setup Virtual CAN (Linux)
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
2. Run the ECU Simulator (Terminal 1)

Bash
python3 ecu_sim.py
The ECU is now listening on ID 0x7E8.

3. Run the Flashing Tool (Terminal 2)
Bash

python3 flash_tool.py
The tool will start the sequence: requesting session, unlocking security, and transferring data.

🔍 Why I built this?
I created this tool to bridge the gap between theoretical knowledge of protocols and real-world application. It demonstrates how Diagnostic Trouble Codes (DTCs) and ECU Reprogramming are handled at the low level, without relying on expensive proprietary tools like Vector CANoe.
