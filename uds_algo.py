# uds_algo.py
# Simulates a proprietary OEM security algorithm

def calculate_key(seed):
    """
    Simple Security Algorithm:
    1. XOR the Seed with a Secret Mask (0x5555)
    2. Bitwise Left Shift by 1
    """
    secret_mask = 0x5555
    
    # Logic: Key = (Seed XOR Mask) << 1
    # We restrict it to 2 bytes (0xFFFF) to mimic standard UDS behavior
    key = (seed ^ secret_mask) << 1
    key = key & 0xFFFF  # Ensure it stays within 16-bit range
    
    return key
