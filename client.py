import isotp
import time

class UDSClient:
    def __init__(self, interface='vcan0'):
        # 1. Setup Addresses
        self.addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x7E8, txid=0x7E0)
        
        # 2. Setup Socket
        self.stack = isotp.socket()
        
        # 3. Configure
        self.stack.set_opts(txpad=0x00)
        
        # 4. Bind
        self.stack.bind(interface, self.addr)

    def close(self):
        self.stack.close()

    # --- FIX: INDENTATION MOVED RIGHT (Now they are inside the Class) ---
    def send_request(self, service_id, sub=None, data=b''):
        payload = bytearray([service_id])
        if sub is not None:
            payload.append(sub)
        if data:
            payload += data
        print(f"\n[CLIENT] Sending: {payload.hex().upper()}")
        self.stack.send(payload)
        return self.receive_response()

    def receive_response(self):
        try:
            self.stack.settimeout(1.0)
            response = self.stack.recv()
            if response:
                print(f"[CLIENT] Received: {response.hex().upper()}")
                if response[0] == 0x7F:
                    print(f"❌ ERROR: Negative Response (NRC: {response[2]:02X})")
                else:
                    print("✅ SUCCESS: Positive Response")
                return response
            else:
                return None
        except:
            print("⚠️ Timeout: ECU is silent")
            return None

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    client = UDSClient()
    try:
        print("--- AUTOMATED DIAGNOSTICS ---")
        
        print("\n[TEST 1] Reading VIN...")
        response = client.send_request(0x22, data=b'\xF1\x90')
        
        if response and response[0] == 0x62:
            vin_data = response[3:]
            vin_text = vin_data.decode('utf-8')
            print(f"   -> VIN: {vin_text}")

        print("\n[TEST 2] Extended Session...")
        # Note: You used 'sub' in your function definition, so we use 'sub' here too.
        client.send_request(0x10, sub=0x03)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        client.close()
