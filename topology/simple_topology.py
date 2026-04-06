#!/usr/bin/env python3
"""
Mininet Topology: 1 Switch, 2 Hosts
"""

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def create_network():
    net = Mininet(switch=OVSKernelSwitch, link=TCLink)

    info('*** Adding Controller\n')
    net.addController(
        name='c0',
        controller=RemoteController,
        ip='127.0.0.1',
        port=6633
    )

    info('*** Adding Switch\n')
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    info('*** Adding Hosts\n')
    h1 = net.addHost('h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
    h2 = net.addHost('h2', ip='10.0.0.2', mac='00:00:00:00:00:02')

    info('*** Adding Links\n')
    net.addLink(h1, s1)
    net.addLink(h2, s1)

    return net

def main():
    setLogLevel('info')
    net = create_network()
    
    info('\n*** Starting Network\n')
    net.start()

    try:
        CLI(net)
    except KeyboardInterrupt:
        pass
    finally:
        info('\n*** Stopping Network\n')
        net.stop()

if __name__ == '__main__':
    main()
