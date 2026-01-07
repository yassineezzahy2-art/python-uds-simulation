import socket
import struct
import random
from uds_algo import calculate_key

# CONFIGURATION
CAN_INTERFACE = "vcan0"
ECU_ID = 0x7E8  # ECU Response ID
TESTER_ID = 0x7E0 # Tester Request ID

# STATE MACHINE
IS_UNLOCKED = False
CURRENT_SEED = 0x0000

def setup_can_socket():
    try:
        sock = socket.socket(socket.AF_CAN, socket.SOCK_RAW, socket.CAN_RAW)
        sock.bind((CAN_INTERFACE,))
        return sock
    except OSError:
        print(f"Error: Could not bind to {CAN_INTERFACE}. Did you run 'sudo modprobe vcan'?")
        exit(1)

def send_response(sock, data):
    can_id = ECU_ID
    # ISO-TP Single Frame Header: Byte 0 = Length of Data
    pci_length = len(data)
    
    # Construct the frame: [PCI_Len] + [UDS_Data] + [Padding]
    frame_data = bytes([pci_length]) + data
    frame_data = frame_data + b'\x00' * (8 - len(frame_data))
    
    can_dlc = 8
    frame = struct.pack("=IB3x8s", can_id, can_dlc, frame_data)
    sock.send(frame)
    print(f"[ECU] Sent: {[hex(x) for x in frame_data]}")

def main():
    global IS_UNLOCKED, CURRENT_SEED
    sock = setup_can_socket()
    print(f"[ECU] Simulation Started on {CAN_INTERFACE}. Waiting for Tester...")

    while True:
        frame, _ = sock.recvfrom(16)
        can_id, can_dlc, data = struct.unpack("=IB3x8s", frame)
        
        if can_id == TESTER_ID:
            rx_data = list(data)
            
            # ISO-TP PARSING (Single Frame)
            # Byte 0 is the Length (PCI). The actual UDS Service ID is at Byte 1.
            pci_len = rx_data[0]
            
            if pci_len == 0: continue # Ignore empty frames
            
            service_id = rx_data[1] # <--- FIXED: Service ID is at Index 1
            
            # Extract just the relevant data for printing
            uds_payload = rx_data[1:pci_len+1]
            print(f"[ECU] Received UDS: {[hex(x) for x in uds_payload]}")

            # ---------------------------------------------------------
            # SERVICE 0x10: DIAGNOSTIC SESSION CONTROL
            # ---------------------------------------------------------
            if service_id == 0x10:
                # Request: [Len] [10] [SubFunc]
                if rx_data[2] == 0x03: # Extended Session
                    # Response: 50 03 (Positive)
                    send_response(sock, bytes([0x50, 0x03, 0x00, 0x32, 0x01, 0xF4]))
                else:
                    send_response(sock, bytes([0x7F, 0x10, 0x12])) # Sub-function not supported

            # ---------------------------------------------------------
            # SERVICE 0x27: SECURITY ACCESS
            # ---------------------------------------------------------
            elif service_id == 0x27:
                sub_function = rx_data[2]
                
                # REQUEST SEED (0x27 0x01)
                if sub_function == 0x01:
                    CURRENT_SEED = random.randint(0x1000, 0xFFFF)
                    seed_high = (CURRENT_SEED >> 8) & 0xFF
                    seed_low = CURRENT_SEED & 0xFF
                    # Response: 67 01 [SEED_HIGH] [SEED_LOW]
                    send_response(sock, bytes([0x67, 0x01, seed_high, seed_low]))

                # SEND KEY (0x27 0x02)
                elif sub_function == 0x02:
                    # Request: [Len] [27] [02] [KeyHigh] [KeyLow]
                    received_key = (rx_data[3] << 8) | rx_data[4]
                    expected_key = calculate_key(CURRENT_SEED)
                    
                    if received_key == expected_key:
                        IS_UNLOCKED = True
                        send_response(sock, bytes([0x67, 0x02])) # Positive Response
                        print("[ECU] *** UNLOCKED SUCCESS ***")
                    else:
                        IS_UNLOCKED = False
                        send_response(sock, bytes([0x7F, 0x27, 0x35])) # NRC 35: Invalid Key
                        print("[ECU] *** WRONG KEY ***")

            # ---------------------------------------------------------
            # SERVICE 0x34: REQUEST DOWNLOAD (Flashing Prep)
            # ---------------------------------------------------------
            elif service_id == 0x34:
                if IS_UNLOCKED:
                    # Positive Response: 74 20 (Max Block Length)
                    send_response(sock, bytes([0x74, 0x20, 0x00, 0x50]))
                    print("[ECU] Ready to Download Firmware...")
                else:
                    send_response(sock, bytes([0x7F, 0x34, 0x33])) # NRC 33: Security Access Denied

            # ---------------------------------------------------------
            # SERVICE 0x36: TRANSFER DATA (The actual Flash)
            # ---------------------------------------------------------
            elif service_id == 0x36:
                if IS_UNLOCKED:
                    block_counter = rx_data[2]
                    # Simulate writing to memory...
                    send_response(sock, bytes([0x76, block_counter]))
                    print(f"[ECU] Writing Data Block {block_counter} to Memory...")
                else:
                    send_response(sock, bytes([0x7F, 0x36, 0x33])) # NRC 33: Access Denied

            # ---------------------------------------------------------
            # SERVICE 0x37: REQUEST TRANSFER EXIT
            # ---------------------------------------------------------
            elif service_id == 0x37:
                send_response(sock, bytes([0x77]))
                print("[ECU] Flash Completed.")

            # ---------------------------------------------------------
            # SERVICE 0x11: ECU RESET
            # ---------------------------------------------------------
            elif service_id == 0x11:
                send_response(sock, bytes([0x51, 0x01]))
                print("[ECU] Resetting System... Goodbye.")
                IS_UNLOCKED = False # Relock after reset

if __name__ == "__main__":
    main()
