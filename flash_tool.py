import socket
import struct
import time
from uds_algo import calculate_key

# CONFIGURATION
CAN_INTERFACE = "vcan0"
TESTER_ID = 0x7E0
ECU_ID = 0x7E8

def setup_can_socket():
    try:
        sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        sock.bind((CAN_INTERFACE,))
        return sock
    except OSError:
        print(f"Error: Could not bind to {CAN_INTERFACE}.")
        exit(1)

def send_request(sock, data):
    can_id = TESTER_ID
    # Add PCI Byte (Length) at the start
    pci_len = len(data)
    frame_data = bytes([pci_len]) + data
    frame_data = frame_data + b'\x00' * (8 - len(frame_data)) # Padding
    
    can_dlc = 8
    frame = struct.pack("=IB3x8s", can_id, can_dlc, frame_data)
    sock.send(frame)
    print(f"\n[TESTER] Request: {[hex(x) for x in frame_data]}")

def receive_response(sock):
    sock.settimeout(2.0)
    try:
        frame, _ = sock.recvfrom(16)
        can_id, can_dlc, data = struct.unpack("=IB3x8s", frame)
        
        if can_id == ECU_ID:
            rx_data = list(data)
            pci_len = rx_data[0]
            uds_response = rx_data[1:pci_len+1]
            print(f"[TESTER] Response: {[hex(x) for x in uds_response]}")
            return uds_response
            
    except socket.timeout:
        print("[TESTER] Error: Timeout - No response from ECU")
        return None

def main():
    sock = setup_can_socket()
    print("=== STARTING UDS FLASHING SEQUENCE ===")

    # STEP 1: Diagnostic Session Control (Extended Session)
    print(">>> STEP 1: Request Extended Session (0x10)")
    send_request(sock, bytes([0x10, 0x03]))
    receive_response(sock)
    time.sleep(0.5)

    # STEP 2: Request Seed (0x27 0x01)
    print(">>> STEP 2: Request Security Seed")
    send_request(sock, bytes([0x27, 0x01]))
    response = receive_response(sock)
    
    if response and response[0] == 0x67:
        # Extract Seed (Bytes 2 and 3)
        seed_high = response[2]
        seed_low = response[3]
        seed = (seed_high << 8) | seed_low
        print(f"[TESTER] Received Seed: {hex(seed)}")

        # Calculate Key
        key = calculate_key(seed)
        key_high = (key >> 8) & 0xFF
        key_low = key & 0xFF
        print(f"[TESTER] Calculated Key: {hex(key)}")

        # STEP 3: Send Key (0x27 0x02)
        print(">>> STEP 3: Send Key to Unlock")
        send_request(sock, bytes([0x27, 0x02, key_high, key_low]))
        auth_resp = receive_response(sock)

        if auth_resp and auth_resp[0] == 0x67:
            print("[TESTER] *** SECURITY UNLOCKED ***")
            
            # STEP 4: Request Download (0x34)
            print(">>> STEP 4: Request Download (Flash Memory)")
            send_request(sock, bytes([0x34, 0x00, 0x44, 0x00, 0x01, 0x00]))
            receive_response(sock)

            # STEP 5: Transfer Data (0x36) - Simulate sending Firmware
            print(">>> STEP 5: Transfer Data (Sending Firmware...)")
            # Sending Block 1
            send_request(sock, bytes([0x36, 0x01, 0xAA, 0xBB, 0xCC, 0xDD]))
            receive_response(sock)
            time.sleep(0.2)
            # Sending Block 2
            send_request(sock, bytes([0x36, 0x02, 0x11, 0x22, 0x33, 0x44]))
            receive_response(sock)

            # STEP 6: Request Transfer Exit (0x37)
            print(">>> STEP 6: Exit Transfer (Flashing Done)")
            send_request(sock, bytes([0x37]))
            receive_response(sock)

            # STEP 7: ECU Reset (0x11)
            print(">>> STEP 7: ECU Reset (Reboot)")
            send_request(sock, bytes([0x11, 0x01]))
            receive_response(sock)

        else:
            print("[TESTER] Authentication Failed.")
    else:
        print("[TESTER] Failed to get Seed.")

if __name__ == "__main__":
    main()
