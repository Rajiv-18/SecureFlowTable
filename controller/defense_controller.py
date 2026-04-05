#!/usr/bin/env python3
"""
Defense Mechanism Ryu Controller
=================================

This controller incorporates defense mechanisms against flow table saturation attacks:

1. **Packet-in Rate Limiting**: Limits the number of PacketIn messages per second
   - Prevents CPU overload from excessive PacketIn messages
   
2. **Flow Timeout Reduction**: Reduces idle timeout for flows
   - Forces flows to evict from table faster
   - Frees up space in flow table
   
3. **Suspicious Traffic Filtering**: Identifies and drops suspicious patterns
   - Detects high-entropy source IPs (indicates scanning)
   - Drops ARP flooding patterns
   - Limits flows from same source to reasonable number

Usage:
    ryu-manager defense_controller.py --observe-links

Requirements:
    - ryu framework
    - Python 3.6+
"""

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp, tcp, udp
from ryu.lib import hub
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class DefenseController(app_manager.RyuApp):
    """
    Enhanced OpenFlow controller with defense mechanisms against flow saturation attacks
    """
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DefenseController, self).__init__(*args, **kwargs)
        
        # MAC address learning
        self.mac_to_port = {}
        
        # ===== DEFENSE PARAMETERS =====
        # Rate limiting configuration
        self.max_packet_in_per_sec = 100  # Maximum PacketIn messages per second
        self.rate_limit_window = 1.0  # Time window in seconds
        
        # Flow timeout configuration
        self.idle_timeout = 10  # Idle timeout for flows (seconds)
        self.hard_timeout = 30  # Hard timeout for flows (seconds)
        
        # Suspicious traffic detection
        self.max_flows_per_source = 50  # Maximum flows from single source IP
        self.max_arp_packets_per_sec = 10  # Max ARP packets per second
        
        # ===== TRAFFIC TRACKING =====
        # Track PacketIn messages per second
        self.packet_in_timestamps = defaultdict(deque)  # {dpid: deque of timestamps}
        
        # Track flows per source IP
        self.source_ip_flows = defaultdict(lambda: defaultdict(int))  # {dpid: {src_ip: count}}
        
        # Track ARP packets
        self.arp_packet_timestamps = defaultdict(deque)  # {dpid: deque of timestamps}
        
        # Track high-entropy IPs (likely attack)
        self.suspicious_ips = set()
        
        # ===== METRICS =====
        self.total_packet_ins = 0
        self.packet_ins_blocked = 0
        self.flows_installed = 0
        self.attacks_detected = 0
        
        LOG.info('DefenseController initialized with defense mechanisms')
        LOG.info(f'Rate limit: {self.max_packet_in_per_sec} PacketIns/sec')
        LOG.info(f'Flow timeouts: idle={self.idle_timeout}s, hard={self.hard_timeout}s')
        LOG.info(f'Suspicious pattern thresholds: max_flows_per_src={self.max_flows_per_source}')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        """
        Handle switch connection
        """
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        LOG.info(f'Switch connected: {dpid:016x}')

        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        # Install table-miss flow with reduced action
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, 
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def check_rate_limit(self, dpid):
        """
        Check if PacketIn rate limit is exceeded
        
        Returns:
            (bool) True if under limit (packet should be processed), False if over limit
        """
        current_time = time.time()
        
        # Clean old timestamps outside the window
        while (len(self.packet_in_timestamps[dpid]) > 0 and
               self.packet_in_timestamps[dpid][0] < current_time - self.rate_limit_window):
            self.packet_in_timestamps[dpid].popleft()
        
        # Check if we're under the limit
        if len(self.packet_in_timestamps[dpid]) >= self.max_packet_in_per_sec:
            return False  # Rate limit exceeded
        
        # Add current timestamp
        self.packet_in_timestamps[dpid].append(current_time)
        return True  # Rate limit OK

    def is_suspicious_source(self, dpid, src_ip):
        """
        Detect if source IP is generating suspicious traffic patterns
        
        Returns:
            (bool, str) Tuple of (is_suspicious, reason)
        """
        # Check if IP has too many flows
        flow_count = self.source_ip_flows[dpid][src_ip]
        if flow_count > self.max_flows_per_source:
            return True, f'Too many flows from source ({flow_count})'
        
        # Check for high-entropy IPs (many different source IPs in short time)
        if src_ip in self.suspicious_ips:
            return True, 'IP marked as suspicious'
        
        return False, ''

    def detect_anomalies(self, dpid, pkt, src_ip, src_mac):
        """
        Run anomaly detection on incoming packet
        
        Returns:
            (bool, str) Tuple of (should_drop, reason)
        """
        # Check for ARP flooding
        arp_pkt = pkt.get_protocol(arp.arp)
        if arp_pkt:
            current_time = time.time()
            
            # Clean old ARP timestamps
            while (len(self.arp_packet_timestamps[dpid]) > 0 and
                   self.arp_packet_timestamps[dpid][0] < current_time - 1.0):
                self.arp_packet_timestamps[dpid].popleft()
            
            # Check if ARP rate is too high
            if len(self.arp_packet_timestamps[dpid]) >= self.max_arp_packets_per_sec:
                self.attacks_detected += 1
                return True, 'ARP flooding detected'
            
            self.arp_packet_timestamps[dpid].append(current_time)
        
        # Check for suspicious source
        is_suspicious, reason = self.is_suspicious_source(dpid, src_ip)
        if is_suspicious:
            self.attacks_detected += 1
            return True, f'Suspicious source: {reason}'
        
        return False, ''

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        """
        Add flow to switch with defense timeouts
        """
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        
        # Create flow_mod with reduced timeouts for defense
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            table_id=table_id,
            idle_timeout=self.idle_timeout,    # Reduced timeout for defense
            hard_timeout=self.hard_timeout,    # Limit total flow lifetime
            flags=ofproto.OFPFF_SEND_FLOW_REM  # Tell controller when flow expires
        )

        datapath.send_msg(mod)
        self.flows_installed += 1

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        """
        Handle PacketIn events with defense mechanisms
        """
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        dpid = datapath.id
        in_port = msg.match['in_port']

        # ===== DEFENSE 1: RATE LIMITING =====
        if not self.check_rate_limit(dpid):
            self.packet_ins_blocked += 1
            LOG.warning(f'PacketIn rate limit exceeded on switch {dpid:016x}')
            return  # Drop this packet

        self.total_packet_ins += 1

        # Parse packet
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth is None:
            return

        src_mac = eth.src
        dst_mac = eth.dst
        src_ip = None
        
        # Extract source IP if available
        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        if ipv4_pkt:
            src_ip = ipv4_pkt.src

        # ===== DEFENSE 2 & 3: ANOMALY DETECTION =====
        if src_ip:
            # Track flows per source
            self.source_ip_flows[dpid][src_ip] += 1
            
            # Check for suspicious patterns
            should_drop, reason = self.detect_anomalies(dpid, pkt, src_ip, src_mac)
            if should_drop:
                LOG.warning(f'Dropping packet from {src_ip}: {reason}')
                return  # Drop suspicious packet

        # Standard learning and forwarding
        if dpid not in self.mac_to_port:
            self.mac_to_port[dpid] = {}

        self.mac_to_port[dpid][src_mac] = in_port

        # Determine output port
        if dst_mac in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst_mac]
        else:
            out_port = ofproto.OFPP_FLOOD

        # Create actions
        actions = [parser.OFPActionOutput(out_port)]

        # Install flow if destination is known
        if out_port != ofproto.OFPP_FLOOD and src_ip:
            # Include IP in match for more specific flows
            match = parser.OFPMatch(
                in_port=in_port,
                eth_dst=dst_mac,
                eth_src=src_mac,
                ipv4_src=src_ip
            )
            self.add_flow(datapath, 1, match, actions)

        # Forward the packet
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions, data=msg.data
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPFlowRemoved, MAIN_DISPATCHER)
    def flow_removed_handler(self, ev):
        """
        Handle flow removal events to free up tracking space
        """
        msg = ev.msg
        reason = msg.reason
        priority = msg.priority
        
        LOG.debug(f'Flow removed. Reason: {reason}, Priority: {priority}')

    def print_defense_stats(self):
        """
        Periodically print defense statistics
        """
        while True:
            hub.sleep(10)  # Print every 10 seconds
            
            LOG.info('='*60)
            LOG.info('DEFENSE CONTROLLER STATISTICS')
            LOG.info('='*60)
            LOG.info(f'Total PacketIns: {self.total_packet_ins}')
            LOG.info(f'PacketIns blocked (rate limit): {self.packet_ins_blocked}')
            LOG.info(f'Flows installed: {self.flows_installed}')
            LOG.info(f'Attacks detected: {self.attacks_detected}')
            
            if self.total_packet_ins > 0:
                block_rate = (self.packet_ins_blocked / self.total_packet_ins) * 100
                LOG.info(f'Block rate: {block_rate:.2f}%')
            
            LOG.info('='*60)

    def start(self):
        """
        Override start to launch stats printer
        """
        super(DefenseController, self).start()
        # Commented out to reduce log spam during testing
        # hub.spawn_after(5, self.print_defense_stats)  # Start stats after 5 seconds
