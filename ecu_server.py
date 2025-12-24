import isotp
import time
import logging

interface = 'vcan0'
addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E0, txid=0x7E8)

# 1. Create the socket
stack = isotp.socket()

# 2. Configure it (MUST BE DONE BEFORE BIND)
stack.set_opts(txpad=0x00)

# 3. Bind it (Plug it in)
stack.bind(interface, addr)

print("✅ Virtual ECU Running...")

current_session = 0x01
security_locked = True
vin_number = b"VF1-DACIA-PROJECT-1"

try:
    while True:
        # I corrected 'playload' to 'payload' to be professional. 
        # It is easier to read.
        payload = stack.recv()
        
        if payload:
            hex_payload = " ".join([f"{byte:02X}" for byte in payload])
            print(f"📥 RECEIVED: [{hex_payload}]")
            
            service_id = payload[0]
            response = bytearray()

            if service_id == 0x10:
                requested_session = payload[1]
                print(f"   Action: Request Session {requested_session:02X}")
                current_session = requested_session
                response = bytearray([0x50, requested_session, 0x00, 0x32, 0x01, 0xF4])

            elif service_id == 0x22:
                did_high = payload[1]
                did_low = payload[2]
                if did_high == 0xF1 and did_low == 0x90:
                    response = bytearray([0x62, 0xF1, 0x90]) + vin_number
                else:
                    response = bytearray([0x7F, 0x22, 0x31])

            elif service_id == 0x3E:
                subf = payload[1]
                if subf == 0x00:
                    response = bytearray([0x7E, 0x00])
                else:
                    continue

            else:
                response = bytearray([0x7F, service_id, 0x11])   

            stack.send(response)
            hex_response = " ".join([f"{byte:02X}" for byte in response])
            print(f"📤 SENT:     [{hex_response}]\n")

except KeyboardInterrupt:                  
    print("\n🛑 ECU Simulator Stopped.")
    stack.close()
