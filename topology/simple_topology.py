#!/usr/bin/env python3
"""
Simple SDN Network Topology using Mininet
==========================================

This script creates a simple SDN network topology:
- 1 OpenFlow-enabled switch
- 2 hosts (h1 and h2)
- 1 Ryu controller (runs on localhost:6633)

The switch connects all hosts and communicates with the controller
using the OpenFlow protocol.

Usage:
    sudo python3 simple_topology.py

Note: Requires Mininet to be installed
"""

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import time

def create_network():
    """
    Create and return a Mininet network with a simple topology
    """
    # Create a network object
    net = Mininet(
        switch=OVSKernelSwitch,
        link=TCLink,  # TCLink allows traffic control (bandwidth, delay, etc.)
    )

    # Add a remote controller that connects to Ryu controller
    # The controller should be running on localhost:6633
    controller = net.addController(
        name='c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )

    info('*** Creating switches\n')
    # Add single switch to network
    s1 = net.addSwitch(
        's1',
        cls=OVSKernelSwitch,
        protocols='OpenFlow13'  # Use OpenFlow 1.3 protocol
    )

    info('*** Creating hosts\n')
    # Add 2 hosts (computers) to the network
    h1 = net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')

    info('*** Creating links\n')
    # Connect hosts to switch
    # Adding bandwidth and delay settings allows us to simulate realistic conditions
    net.addLink(h1, s1, bw=100)  # 100 Mbps bandwidth
    net.addLink(h2, s1, bw=100)

    return net

def main():
    """
    Main function: Create network, start it, and wait for user input
    """
    # Set logging level to see informative messages
    setLogLevel('info')

    info('\n*** Creating Network Topology\n')
    net = create_network()

    info('\n*** Starting Network\n')
    net.start()

    info('\n*** Network is running\n')
    info('*** To test connectivity, run: h1 ping h2\n')
    info('*** To stop network, type: exit\n')

    try:
        # Start CLI (Command Line Interface) - allows interactive commands
        CLI(net)
    except KeyboardInterrupt:
        info('\n*** Shutting down due to keyboard interrupt\n')
    finally:
        info('\n*** Stopping Network\n')
        net.stop()
        info('*** Network stopped\n')

if __name__ == '__main__':
    main()
