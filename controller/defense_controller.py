#!/usr/bin/env python3
"""
SDN Defense Controller: Implements Rate Limiting, Flow Timeouts, and Anomaly Detection
"""

import logging
import time
from collections import defaultdict, deque
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, arp

logging.basicConfig(level=logging.INFO)
LOG = logging.getLogger(__name__)

class DefenseController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(DefenseController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        
        # Defense parameters
        self.max_packet_in_per_sec = 100
        self.rate_limit_window = 1.0
        self.idle_timeout = 10
        self.hard_timeout = 30
        self.max_flows_per_source = 50
        self.max_arp_packets_per_sec = 10
        
        # State tracking
        self.packet_in_timestamps = defaultdict(deque)
        self.source_ip_flows = defaultdict(lambda: defaultdict(int))
        self.arp_packet_timestamps = defaultdict(deque)
        
        # Metrics
        self.total_packet_ins = 0
        self.packet_ins_blocked = 0
        self.flows_installed = 0
        self.attacks_detected = 0
        
        LOG.info('DefenseController initialized')

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        LOG.info(f'Switch connected: {dpid:016x}')
        self.mac_to_port.setdefault(dpid, {})

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def check_rate_limit(self, dpid):
        now = time.time()
        timestamps = self.packet_in_timestamps[dpid]
        while timestamps and timestamps[0] < now - self.rate_limit_window:
            timestamps.popleft()
        
        if len(timestamps) >= self.max_packet_in_per_sec:
            return False
        
        timestamps.append(now)
        return True

    def detect_anomalies(self, dpid, pkt, src_ip):
        # ARP flood detection
        if pkt.get_protocol(arp.arp):
            now = time.time()
            timestamps = self.arp_packet_timestamps[dpid]
            while timestamps and timestamps[0] < now - 1.0:
                timestamps.popleft()
            
            if len(timestamps) >= self.max_arp_packets_per_sec:
                return True, 'ARP flooding'
            timestamps.append(now)
        
        # Source flow limit detection
        if src_ip and self.source_ip_flows[dpid][src_ip] > self.max_flows_per_source:
            return True, f'Flow limit exceeded for {src_ip}'
        
        return False, ''

    def add_flow(self, datapath, priority, match, actions, table_id=0):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=priority,
            match=match,
            instructions=inst,
            table_id=table_id,
            idle_timeout=self.idle_timeout,
            hard_timeout=self.hard_timeout,
            flags=ofproto.OFPFF_SEND_FLOW_REM
        )
        datapath.send_msg(mod)
        self.flows_installed += 1

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        in_port = msg.match['in_port']

        # Rate limiting
        if not self.check_rate_limit(dpid):
            self.packet_ins_blocked += 1
            LOG.warning(f'Rate limit exceeded on {dpid:016x}')
            return

        self.total_packet_ins += 1
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if not eth:
            return

        ipv4_pkt = pkt.get_protocol(ipv4.ipv4)
        src_ip = ipv4_pkt.src if ipv4_pkt else None

        # Anomaly detection
        if src_ip:
            self.source_ip_flows[dpid][src_ip] += 1
            should_drop, reason = self.detect_anomalies(dpid, pkt, src_ip)
            if should_drop:
                self.attacks_detected += 1
                LOG.warning(f'Dropping packet: {reason}')
                return

        src_mac, dst_mac = eth.src, eth.dst
        self.mac_to_port[dpid][src_mac] = in_port

        # Forwarding logic
        out_port = self.mac_to_port[dpid].get(dst_mac, datapath.ofproto.OFPP_FLOOD)
        actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]

        if out_port != datapath.ofproto.OFPP_FLOOD and src_ip:
            match = datapath.ofproto_parser.OFPMatch(
                in_port=in_port, eth_dst=dst_mac, eth_src=src_mac, ipv4_src=src_ip
            )
            self.add_flow(datapath, 1, match, actions)

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id, in_port=in_port,
            actions=actions, data=msg.data
        )
        datapath.send_msg(out)
