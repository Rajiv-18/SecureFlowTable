#!/usr/bin/env python3
"""
Basic Ryu SDN Controller
========================

This is a simple OpenFlow controller that:
1. Listens for switch connections
2. Responds to PacketIn events (unknown packets)
3. Installs basic forwarding rules
4. Logs traffic information

The controller runs on port 6633 (standard OpenFlow port).

Usage:
    ryu-manager basic_controller.py --observe-links

Note: Requires ryu to be installed
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp
from ryu.lib import hub
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class BasicController(app_manager.RyuApp):
    """
    Basic OpenFlow controller for simple L2 forwarding
    
    This controller learns MAC addresses and builds a forwarding table,
    similar to a switch. It's useful for understanding basic OpenFlow operations.
    """
    
    # Specify OpenFlow version
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(BasicController, self).__init__(*args, **kwargs)
        
        # Dictionary to store MAC address to port mappings
        # Format: {datapath_id: {mac_address: port}}
        self.mac_to_port = {}
        
        # Metrics to track
        self.packet_in_count = 0
        self.flow_count = 0
        self.start_time = time.time()
        
        LOG.info("BasicController initialized")

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Handle switch connection event.
        
        When a switch connects to controller, we install a default rule
        to send unknown packets to the controller.
        """
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Get the datapath ID (switch identifier)
        dpid = datapath.id
        LOG.info(f'Switch connected: {dpid:016x}')

        # Initialize MAC to port mapping for this switch
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        # Install default flow rule that sends packets to controller if no rule matches
        # This is called a "table_miss" flow
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions, table_id=0)

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        """
        Add a flow entry to the switch's flow table.
        
        Args:
            datapath: The switch to add the flow to
            priority: Priority of the flow (higher = checked first)
            match: Matching criteria for the flow
            actions: Actions to take on matching packets
            table_id: Which flow table to add to (default: 0)
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Create a flow_mod message
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            table_id=table_id,
            hard_timeout=0,
            idle_timeout=60  # Flow times out after 60 seconds of inactivity
        )

        # Send the flow modification message to the switch
        datapath.send_msg(mod)
        self.flow_count += 1
        LOG.debug(f'Flow added. Total flows: {self.flow_count}')

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handle PacketIn event.
        
        When a packet arrives at the switch that doesn't match any flow rule,
        the switch sends it to the controller. This function handles it.
        
        It learns the source MAC and forward the packet appropriately.
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        # Increment packet-in counter
        self.packet_in_count += 1
        elapsed_time = time.time() - self.start_time

        # Parse the packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        # Only process ethernet frames
        if eth is None:
            return

        src_mac = eth.src
        dst_mac = eth.dst

        LOG.info(f'PacketIn #{self.packet_in_count} from {src_mac} to {dst_mac} '
                 f'on port {in_port} (elapsed: {elapsed_time:.2f}s)')

        # Learn the port for the source MAC
        self.mac_to_port[dpid][src_mac] = in_port

        # Determine output port
        if dst_mac in self.mac_to_port[dpid]:
            # We know the destination port
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            # Destination unknown, flood to all ports except incoming port
            out_port = ofproto.OFPP_FLOOD

        # Create actions for the packet
        actions = [parser.OFPActionOutput(out_port)]

        # If we know the destination, install a flow rule to avoid future PacketIns
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst_mac, eth_src=src_mac)
            self.add_flow(datapath, 1, match, actions)

        # Send the packet out
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions, data=msg.data
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """
        Handle flow statistics reply from switch.
        This is called when we request flow statistics from the switch.
        """
        stats = ev.msg.body
        LOG.debug(f'Flow stats: {len(stats)} flows in table')

def print_stats():
    """
    Periodically print controller statistics (can be extended)
    """
    while True:
        hub.sleep(10)  # Print every 10 seconds
        LOG.info(f'Controller stats - PacketIns: {BasicController.packet_in_count}, '
                 f'Flows: {BasicController.flow_count}')
